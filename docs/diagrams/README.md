# Diagrams

Generated with [Noodle](https://github.com/TheGostsniperfr/noodle) from `docs/architecture/system/`
(model and views). Do not edit the `.drawio` or `.svg` files by hand: change the YAML, then

```bash
cd docs
for v in workflow layers; do
  noodle render architecture/system -view $v            # lint
  for t in dark light; do
    noodle render architecture/system -view $v -theme $t -o diagrams/$v.$t.drawio
    drawio -x -f svg --embed-diagram -o diagrams/$v.$t.drawio.svg diagrams/$v.$t.drawio
  done
done
```
