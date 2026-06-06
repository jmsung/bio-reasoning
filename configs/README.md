# configs/

Experiment configurations (YAML). One file per experiment so runs are
reproducible from a config hash.

Convention: `configs/<track>_<model>_<variant>.yaml` (e.g.
`a_baseline.yaml`, `b_lora_v1.yaml`).

A loader (Hydra or plain `yaml.safe_load`) will be added once the first
real experiment lands — keep it simple until then.
