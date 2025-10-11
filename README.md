# OpenFahrplan
<img src="src/openfahrplan/assets/favicon2.png" width="256">

OpenFahrplan is a pet project to explore the technologies and challenges behind public transport IT systems.
Keep reading to see how the idea formed, what I learned about public transport, and the challenges I encountered while
implementing a python based web app to plan trips with public transport.

## Development
```shell
poetry install
docker buildx build --platform linux/amd64,linux/arm64 -t ghcr.io/danielr1996/openfahrplan:latest --push .
helm upgrade --install --create-namespace -n openfahrplan openfahrplan chart/
```

## License and Attribution
### Source Code / Software
All source code in this repository authored by the project’s contributors is licensed under the [MIT License](./LICENSE.md).

Third-party packages installed via package managers (e.g. npm, pip, crates.io) remain subject to their own respective licenses as provided by their authors and distributors.

### Data
This repository also contains non-code materials subject to different licensing terms:

- `data/parquet/vgn` — [© VGN – Verkehrsverbund Großraum Nürnberg GmbH](https://www.vgn.de/web-entwickler/open-data/), licensed under [Creative Commons Attribution 3.0 Germany (CC BaY 3.0 DE)](https://creativecommons.org/licenses/by/3.0/de/), converted to parquet format.
- `data/parquet/gtfsde` —  [GTFS.DE](https://gtfs.de), licensed under [Creative Commons 4.0](https://creativecommons.org/licenses/by/4.0/), converted to parquet format.
