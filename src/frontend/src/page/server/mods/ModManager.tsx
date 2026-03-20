{% extends "base.j2" %}

{% block title %}{{ server.name }} • Mods{% endblock %}

{% block content %}
<div class="container-inner">
  <div class="medium-center">
    <div class="panel mb64 flex flex-column">
      <div class="flex" style="align-items: center; gap: 16px; flex-wrap: wrap;">
        <div class="flex flex-column" style="gap: 4px;">
          <p class="muted mb0">Installed Mods</p>
          <h2 class="mt0 mb0">{{ server.name }} Loadout</h2>
          <p class="mt0">Review the mods currently packaged with this server.</p>
        </div>
        <a class="button button-ghost" style="margin-left: auto;" href={`/servers/${name}`}>Back to Server</a>
      </div>
      <div class="panel-inset-lighter mt24" style="padding: 24px;">
        <div class="flex" style="justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <span>Factorio version: <strong>{{ factorio_version or 'Unknown' }}</strong></span>
          <span>Total mods: <strong>{{ installed_mods|length }}</strong></span>
        </div>
        <hr>
        <div id="installed-mods">
          {% include "server/mods/_installed_list.j2" %}
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
