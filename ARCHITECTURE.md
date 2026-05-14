# DouyinLiveRecorder — Architecture

This document describes the post-refactor architecture of DouyinLiveRecorder.
The previous monolithic `main.py` (2196 LOC, single 1100-line `start_record`
function with 50+ platform branches) has been split into the
[`src/app/`](src/app/) package consisting of single-responsibility modules.

## Module map

| Module | LOC | Responsibility |
| --- | ---: | --- |
| `main.py` | 20 | Process entry — delegates to `src.app.bootstrap.run()`. |
| `src/app/__init__.py` | 47 | Package docstring & `__all__`. |
| `src/app/state.py` | 241 | Shared mutable state, runtime metadata, platform host catalogues. |
| `src/app/config.py` | 203 | INI loading; populates `state` attributes. |
| `src/app/file_ops.py` | 128 | URL/config file mutation primitives + backup loop. |
| `src/app/url_loader.py` | 140 | Parses `URL_config.ini` → `(quality, url, name)` triples. |
| `src/app/naming.py` | 81 | Pure helpers: name cleaning, quality codes, header/source picking. |
| `src/app/proxy_resolver.py` | 37 | Per-stage proxy decision (monitoring vs recording). |
| `src/app/notifier.py` | 49 | Multi-channel push (WeChat/DingTalk/Email/TG/BARK/NTFY/PushPlus). |
| `src/app/post_process.py` | 129 | ffmpeg transcoding / segmenting / subtitle generation. |
| `src/app/ffmpeg_runner.py` | 202 | ffmpeg subprocess driver + direct httpx FLV download. |
| `src/app/monitor.py` | 91 | Dashboard display + dynamic `max_request` adjustment threads. |
| `src/app/platform_handlers_cn.py` | 294 | Domestic platform handler functions. |
| `src/app/platform_handlers_os.py` | 208 | Overseas platform handler functions. |
| `src/app/platform_registry.py` | 87 | `(url_substring → handler)` lookup table. |
| `src/app/platform_dispatch.py` | 49 | Thin facade exposing `dispatch()` + `UnknownPlatformError`. |
| `src/app/recorder_format.py` | 173 | Per-format ffmpeg command generators (FLV/MKV/MP4/TS). |
| `src/app/recorder_pipeline.py` | 205 | ffmpeg base / save-path / audio / direct-FLV pipelines. |
| `src/app/recorder.py` | 274 | `start_record()` per-URL recording loop. |
| `src/app/bootstrap.py` | 116 | Top-level `run()` & main scheduling loop. |

All modules are kept ≤ 300 LOC; the `main.py` entry is 20 LOC, well under the
100-LOC cap.

## Dependency graph

The package is layered. Arrows below mean "imports from"; the graph is
acyclic.

```
            ┌──────────────────────────┐
            │         main.py          │
            └────────────┬─────────────┘
                         │
                         ▼
            ┌──────────────────────────┐
            │     app.bootstrap        │
            └────────┬───────┬─────────┘
                     │       │
              ┌──────▼──┐  ┌─▼──────────┐
              │ monitor │  │ recorder   │
              └────┬────┘  └─┬────────┬─┘
                   │         │        │
                   │   ┌─────▼──┐  ┌──▼──────────────────┐
                   │   │notifier│  │ recorder_pipeline   │
                   │   └────────┘  └─┬───────────────┬───┘
                   │                 │               │
                   │       ┌─────────▼────┐  ┌───────▼──────┐
                   │       │recorder_fmt  │  │ ffmpeg_runner│
                   │       └─────────┬────┘  └───────┬──────┘
                   │                 │               │
                   │                 ▼               ▼
                   │       ┌──────────────────────────────┐
                   │       │       post_process           │
                   │       └──────────────────────────────┘
                   │
                   │       ┌──────────────────────────────┐
                   └──────▶│   platform_dispatch          │
                           └─────────────┬────────────────┘
                                         │
                                         ▼
                           ┌──────────────────────────────┐
                           │     platform_registry        │
                           └──────┬──────────────┬────────┘
                                  │              │
                       ┌──────────▼─┐    ┌───────▼────────┐
                       │handlers_cn │    │ handlers_os    │
                       └────────────┘    └────────────────┘

  shared by every module:  app.state  ←  app.naming, app.proxy_resolver,
                                          app.file_ops, app.url_loader,
                                          app.config
```

## Public API contracts

Each module exposes a small, intentional surface:

- `state` — attribute namespace; mutate as `state.x = value`.
- `config.load(parser=None)` — populates `state` from `config/config.ini`.
- `url_loader.parse_url_config()` — appends triples to
  `state.url_tuples_list`.
- `naming.{clean_name, get_quality_code, get_record_headers,
  is_flv_preferred_platform, select_source_url, contains_url}` — pure
  functions, all unit-tested.
- `proxy_resolver.get_stage_proxy_address(url, enable)` — pure function.
- `platform_dispatch.dispatch(url, quality, proxy)` →
  `(platform, port_info, new_url)` or raises `UnknownPlatformError`.
- `recorder.start_record(url_data, count)` — recorder thread target.
- `bootstrap.run()` — main entry, called from `main.py`.

## Tests

Pytest suites live under [`tests/`](tests/). Run them with:

```bash
python3 -m pytest tests/ -q
```

Coverage focuses on pure / file helpers:

- `tests/test_naming.py` — quality codes, name cleaning, header/source picking,
  URL detection.
- `tests/test_proxy_resolver.py` — every code path of stage proxy resolution.
- `tests/test_url_loader.py` — INI parsing for plain URL, qualified URL,
  comment lines and unknown hosts.
- `tests/test_file_ops.py` — `update_file`, `delete_line`, proxy-env scrubbing,
  backup rotation.

The recorder loop, ffmpeg subprocess driver, platform handlers and bootstrap
loop are intentionally excluded from unit tests because they require live
network access or running ffmpeg; they are covered by the existing manual
end-to-end smoke tests.

## Backwards compatibility

`python main.py` continues to work as before. All configuration files
(`config/config.ini`, `config/URL_config.ini`) and recorded output paths are
unchanged. Public behaviour, including platform-specific quirks, ffmpeg flag
ordering and message templates, was preserved verbatim.
