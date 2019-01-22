## Config Server in Python

Inspired by Netflix Config Server.

### About

Flask web application that serves configuration from configuration repository.

For example, your configuration repository has `dev.yml` file with following content:
```yml
redis:
  host: 127.0.0.1
  port: 6379
```

Config server will transform it into `GET /dev` route and response in JSON format:
```json
{
    "redis": {
        "host": "127.0.0.1",
        "port": 6379
    }
}
```

It only supports Github public repositories at the moment and uses Github Webhooks to update configuration settings of config server.

You can test it live. Go to [repository](https://github.com/artemrys/config-server-example). It is public, so you can commit there and see changes live in already deployed application on Heroku.

Restrictions:

 * only `*.yml` files
 * only `master` branch
 * only first level tree (no folders)

### Setup

Environmental variables:

 * GITHUB_ACCESS_TOKEN - from [here](https://github.com/settings/tokens)
 * GITHUB_CONFIG_REPO - your configuration repository name


#### Testing locally

Install [ngrok](https://ngrok.com/) and run command `ngrok http 5000`.

It will give you a public address so you can set it as a Github Webhook url.

Then you need to run the application with environmental variables set and correct.

And then, if you do a commit to your repository with configuration, you will see the changes in your local web Flask application.