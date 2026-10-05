# Third-party notices

The MIT License in this repository applies to original HearAround project source code and documentation unless a file states otherwise. It does not relicense third-party models, datasets, audio, libraries, trademarks, or service content.

## Demo audio

Bundled demo WAV files are normalized derivatives of Public Domain, CC0, and CC BY source recordings. Each file's creator, license, source URL, and transformation metadata are recorded in:

- `data/ATTRIBUTION.md`
- `data/manifest.csv`

The CC BY recording must retain its attribution when redistributed. Mixed clips retain the licenses of all contributing recordings.

## Holdout evaluation audio

Holdout audio and downloaded source files are excluded from the public repository. Aggregate metrics, manifests, attribution, failure reports, and reproducible collection scripts remain available. Source licenses and URLs are listed in `eval/HOLDOUT_ATTRIBUTION.md` and `eval/holdout_manifest.csv`.

## Model and software dependencies

HearAround loads the YAMNet model from TensorFlow Hub and uses AudioSet class names. TensorFlow, TensorFlow Hub, YAMNet, AudioSet, FastAPI, and all other dependencies remain governed by their respective upstream licenses and terms. Dependency version ranges are listed in `backend/requirements.txt` and `backend/requirements-dev.txt`.

Product and organization names are used only for identification and remain the property of their respective owners.
