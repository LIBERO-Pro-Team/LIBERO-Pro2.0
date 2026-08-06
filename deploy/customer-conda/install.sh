#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "$0")" && pwd)"
prefix="${1:-${LIBERO_PRO_CONDA_PREFIX:-${HOME}/.conda/envs/libero-pro2}}"
export CONDA_NO_PLUGINS=true

command -v conda >/dev/null 2>&1 || {
  echo "Conda is required and must be available on PATH." >&2
  exit 1
}
[[ -f "$root_dir/environment.yml" ]] || {
  echo "environment.yml is missing from the delivery bundle." >&2
  exit 1
}
[[ -f "$root_dir/requirements-lock.txt" ]] || {
  echo "requirements-lock.txt is missing from the delivery bundle." >&2
  exit 1
}
for source_dir in service-source simulator-source; do
  [[ -d "$root_dir/$source_dir" ]] || {
    echo "$source_dir is missing from the delivery bundle." >&2
    exit 1
  }
done

if [[ -x "$prefix/bin/python" ]]; then
  conda env update --solver classic --prefix "$prefix" --file "$root_dir/environment.yml"
else
  conda env create --solver classic --yes --prefix "$prefix" --file "$root_dir/environment.yml"
fi

conda run --prefix "$prefix" python -m pip install \
  --requirement "$root_dir/requirements-lock.txt"
conda run --prefix "$prefix" python -m pip install \
  --no-build-isolation --no-deps --editable "$root_dir/simulator-source"
conda run --prefix "$prefix" python -m pip install \
  --no-build-isolation --no-deps --editable "$root_dir/service-source"

printf 'Installed LIBERO-PRO v1.0.0 into %s\n' "$prefix"
printf 'Next: bash %s/configure.sh %s\n' "$root_dir" "$prefix"
