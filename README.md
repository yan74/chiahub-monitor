# chiahub-monitor

The official chia pooling protocol allows a pool to only **estimate** the plot size for a
farmer. That's why we created a small helper program that connects to your farmer and retrieves the actual number of
plots you have. We don't use this to calculate your share (still using the official pooling protocol) but it enables the
pool to warn you if your actual plot size differs a lot from your estimated plot size. We believe in transparency that's why
we made this little helper open-source

## Installation

1. Install Python3
2. Create and activate a new environment, then install chiahub-monitor

```
python -m venv venv
source venv/bin/activate (Windows: venv\Scripts\activate.bat)
pip install chiahub_monitor
```

3. Start with

```
python -m chiahub_monitor.main
```

Chiahub-monitor will automatically find your chia config.yaml and use it to connect to the local running farmer. Upon
retrieving plots known to the farmer it will upload that list to your farmers profile at chiahub.io.