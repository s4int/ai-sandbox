
## Install [promptfoo](https://www.promptfoo.dev/docs/intro/):

```shell
brew install promptfoo
```

It is preconfigured to use ollama providers:
- ollama:chat:llama3.1:8b
- ollama:chat:gpt-oss:20b

You can edit `promptfooconfig.yaml` to modify tests.

Then run:
```shell
promptfoo eval
```

To skip cache:
```shell
promptfoo eval --no-cache
```

Afterwards, you can view the results by running:
```shell
promptfoo view
```
