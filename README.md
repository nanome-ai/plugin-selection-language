# Nanome - Selection Language (MDAnalysis)

Nanome plugin to input a selection query and select the corresponding atoms in Nanome

## Dependencies

[Docker](https://docs.docker.com/get-docker/)

**TODO**: Provide instructions on how to install and link any external dependencies for this plugin.

**TODO**: Update docker/Dockerfile to install any necessary dependencies.

## Usage

To run Selection Language (MDAnalysis) in a Docker container:

```sh
$ cd docker
$ ./build.sh
$ ./deploy.sh -a <plugin_server_address> [optional args]
```

### Optional arguments:

- `-x arg`

  Example argument documentation

**TODO**: Add any optional argument documentation here, or remove section entirely.

## Development

To run Selection Language (MDAnalysis) with autoreload:

```sh
$ python3 -m pip install -r requirements.txt
$ python3 run.py -r -a <plugin_server_address> [optional args]
```

## License

MIT
