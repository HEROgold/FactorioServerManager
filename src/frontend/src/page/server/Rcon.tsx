{% extends "base.j2" %}

{% block title %}{{ server.name }} RCON{% endblock %}

{% block content %}
<div class="container-inner">
  <div class="panel mb64 flex flex-column">
    <div class="flex" style="align-items: center; gap: 16px; flex-wrap: wrap;">
      <div class="flex flex-column" style="gap: 4px;">
        <h2 class="mb0">{{ server.name }} RCON</h2>
        <p class="mt0 mb0">Use these credentials to connect with any RCON client.</p>
      </div>
      <div class="server-subnav" style="margin-left: auto; display: flex; gap: 12px;">
        <a class="button button-ghost" href={`/servers/${name}`}>Back to Server</a>
        <a class="button button-ghost" href={`/servers/${name}/logs`}">View Logs</a>
      </div>
    </div>
    <div class="panel-inset-lighter mt24" style="padding: 24px; display: grid; gap: 32px;">
      <section>
        <h3 class="mt0">Connection Details</h3>
        <div class="connection-grid" style="display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));">
          <div class="detail-card" style="background: #111; color: #f1f1f1; padding: 16px; border-radius: 6px; display: flex; flex-direction: column; gap: 8px;">
            <span class="label" style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; color: #ababab;">Host</span>
            <code style="font-size: 0.95rem;">{{ server.ip }}</code>
            <button class="button" style="align-self: flex-start;" onclick="copyToClipboard('{{ server.ip }}')">Copy Host</button>
          </div>
          <div class="detail-card" style="background: #111; color: #f1f1f1; padding: 16px; border-radius: 6px; display: flex; flex-direction: column; gap: 8px;">
            <span class="label" style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; color: #ababab;">Port</span>
            <code style="font-size: 0.95rem;">{{ server.settings.rcon_port }}</code>
            <button class="button" style="align-self: flex-start;" onclick="copyToClipboard('{{ server.settings.rcon_port }}')">Copy Port</button>
          </div>
          <div class="detail-card" style="background: #111; color: #f1f1f1; padding: 16px; border-radius: 6px; display: flex; flex-direction: column; gap: 8px;">
            <span class="label" style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; color: #ababab;">Password</span>
            {% if rcon_password %}
            <code style="font-size: 0.95rem;">{{ rcon_password }}</code>
            <button class="button" style="align-self: flex-start;" onclick="copyToClipboard('{{ rcon_password }}')">Copy Password</button>
            {% else %}
            <p class="mb0">Password file missing. Launch the server once to generate it.</p>
            {% endif %}
          </div>
        </div>
      </section>
      <section>
        <h3 class="mt0">Quick Start</h3>
        <p class="mt0">Point your preferred RCON tooling (Factorio headless client, <code>factorio-rcon</code>, mcrcon, etc.) to the host and port above, then authenticate with the password.</p>
        <div class="panel" style="background: #080b12; color: #d7d7d7; padding: 16px; border-radius: 6px;">
          <p class="mt0 mb8" style="font-size: 0.85rem; letter-spacing: 0.04em; text-transform: uppercase; color: #9fb3ff;">Example CLI</p>
          <pre style="margin: 0; font-size: 0.9rem; overflow-x: auto;">factorio-rcon --host {{ server.ip }} --port {{ server.settings.rcon_port }} --password {{ rcon_password or '"<password>"' }} "/help"</pre>
        </div>
        <p class="mb0" style="font-size: 0.85rem; color: #999;">Keep credentials private; anyone with this password can run commands on your server.</p>
      </section>
    </div>
  </div>
</div
{% endblock %}
