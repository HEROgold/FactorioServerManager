interface Props {
  title?: string;
}

export function Head({ title = "Factorio Server Manager" }: Props) {
  return (
    <head>
      <title>{title}</title>
      <meta charSet="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <script
        src="https://cdn.jsdelivr.net/npm/htmx.org@2.0.8/dist/htmx.min.js"
        integrity="sha384-/TgkGk7p307TH7EXJDuUlgG3Ce1UVolAOFopFekQkkXihi5u/6OCvVKyz1W+idaz"
        crossOrigin="anonymous"
      ></script>
      <link rel="stylesheet" href="/static/css/main.css" />
    </head>
  );
}
