# StageTool API
RESTful API handless communication between StageTool Core and StageTool UI. StageTool is a convolutional deep neural network-based approach that facilitates the analysis of spermatogenesis in DAPI-stained mouse testis cross-sections.

![stagetool-architecture-diagram](https://github.com/Turku-BioImaging/stagetool-api/assets/11444749/637b64dd-c24b-4181-b67e-3754259eb91f)

## Dev / Testing

Create a `.env` inside `./src` with the following keys

```
ENV=development // can be "production" or "staging"
DOCKER_IMAGE_NAME=ghcr.io/turku-bioimaging/stagetool-core
DOCKER_IMAGE_VERSION=0.1.0
```
