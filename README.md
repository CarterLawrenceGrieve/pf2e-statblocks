# PF2e Stat Blocks

Search [Archives of Nethys](https://2e.aonprd.com/Creatures.aspx) for Pathfinder 2e creatures and print their stat blocks, several to a page.

## Run

Needs Python 3.9+ (standard library only) and an internet connection.

```
python statblocks.py
```

On Windows you can double-click `Start Stat Blocks.cmd`. The app opens at http://127.0.0.1:8765. Keep the window running while you use it.

The local server is required: AoN's search backend rejects requests from other websites, so `statblocks.py` fetches the data and hands it to the page.

## Use

- Search by name and click a result, or paste a list of names / AoN links under "Add a list at once".
- Reorder or remove creatures, or sort by level.
- Choose 1–3 columns, Letter or A4, portrait or landscape, and text size.
- Optional: description and Recall Knowledge DCs, lore sidebars, source line, ink saver, and letting long blocks split across columns.
- Click **Print**. Turn off the browser's "Headers and footers" for a clean page.

Selection and settings are remembered in the browser.

Creature data © Paizo Inc., served by Archives of Nethys. This is an unofficial tool.
