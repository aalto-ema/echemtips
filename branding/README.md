# eChemTips artwork

The three original vector concepts in `concepts/` were proposed for issue #15.
The operator approved **C — electrochemical response** on 20 October 2026; its
canonical runtime source is `echemtips/assets/echemtips-logo.svg`.
Their artwork is available under the repository
MIT license. They use a navy/white/mint palette, no external fonts or stock assets.
Meaning never depends on colour alone. A: meniscus contact (recommended, simplest
small mark); B: spatial array; C: electrochemical response.

Both
applications and About already share `echemtips.branding`; replacement should
happen there, not by adding app-specific images.

Generate multi-resolution Windows ICO and macOS ICNS, plus PNG sizes, with:

```bash
python scripts/export_app_icons.py --output dist/icons
# After approval, explicitly select a vector source:
python scripts/export_app_icons.py --source branding/concepts/contact.svg --output dist/proposed-icons
```

This exports artwork only: it does not change the app logo. Inspect 16, 20, 24,
32, 48 and 256 px on white and navy before approval. Windows builds use the current
logo through the same exporter. No branding change affects instrument behaviour.
