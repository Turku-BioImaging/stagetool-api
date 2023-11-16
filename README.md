# StageTool API

REST API for StageTool, a convolutional deep neural network-based approach that facilitates the analysis of spermatogenesis in DAPI-stained mouse testis cross-sections.

StageTool API handles communication between StageTool Core and StageTool UI.

## Dev / Testing

Create a `.env` inside `./src` with the following keys

```
ENV=development // can be "production" or "staging"
DOCKER_IMAGE_NAME=ghcr.io/turku-bioimaging/stagetool-core
DOCKER_IMAGE_VERSION=0.1.0
```
