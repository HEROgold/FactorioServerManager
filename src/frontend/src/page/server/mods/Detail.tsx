{% if error %}
<div class="mod-alert">{{ error }}</div>
{% elif not mod %}
<div class="mod-detail-placeholder">
    <h4>No detail available.</h4>
    <p>Select a mod from the search results to preview installable releases.</p>
</div>
{% else %}
<article class="mod-detail-card">
    <header>
        <div>
            <p class="mod-eyebrow">{{ mod.category|title if mod.category else 'Mod' }}</p>
            <h3>{{ mod.title or mod.name }}</h3>
            <p>{{ mod.summary }}</p>
        </div>
        {% if mod.thumbnail %}
        <div class="mod-detail-thumb" role="presentation" style="background-image: url('{{ mod.thumbnail }}');"></div>
        {% endif %}
    </header>
    {% if mod.tags %}
    <div class="mod-detail-tags">
        {% for tag in mod.tags %}
        <span class="mod-pill outline">{{ tag }}</span>
        {% endfor %}
    </div>
    {% endif %}
    {% if releases %}
    <form
        class="mod-install-form"
        hx-post={`/servers/${name}/mods/install/${mod_id}`}
        hx-target="#installed-mods"
        hx-swap="innerHTML"
        hx-indicator="#mods-installed-indicator"
    >
        <input type="hidden" name="mod_name" value="{{ mod.name }}">
        <label>
            <span>Choose release</span>
            <select name="version">
                {% for release in releases %}
                <option value="{{ release.version }}" {% if release.is_recommended %}selected{% endif %}>
                    v{{ release.version }} • Factorio {{ release.factorio_version or 'any' }} • {{ release.released_at }}
                </option>
                {% endfor %}
            </select>
        </label>
        <button class="button" type="submit" {% if token_missing %}disabled{% endif %}>Install to server</button>
    </form>
    {% if token_missing %}
    <p class="mod-token-warning">Log in with a Factorio account to download this mod.</p>
    {% endif %}
    <div class="mod-release-list">
        {% for release in releases %}
        <div class="mod-release-row{% if release.is_recommended %} recommended{% endif %}">
            <strong>v{{ release.version }}</strong>
            <span>Factorio {{ release.factorio_version or 'any' }}</span>
            <span>{{ release.released_at }}</span>
            {% if release.size_label %}
            <span>{{ release.size_label }}</span>
            {% endif %}
        </div>
        {% endfor %}
    </div>
    {% else %}
    <div class="mod-placeholder">
        <p>No releases are available for this mod yet.</p>
    </div>
    {% endif %}
    {% if releases %}
    {% set ns = namespace(primary=None) %}
    {% for release in releases %}
        {% if release.is_recommended and ns.primary is none %}
            {% set ns.primary = release %}
        {% endif %}
    {% endfor %}
    {% if ns.primary is none %}
        {% set ns.primary = releases[0] %}
    {% endif %}
    {% if ns.primary and ns.primary.dependencies %}
    <section class="mod-dependencies">
        <h4>Key dependencies</h4>
        <ul>
            {% for dep in ns.primary.dependencies[:6] %}
            <li>{{ dep }}</li>
            {% endfor %}
        </ul>
    </section>
    {% endif %}
    {% endif %}
</article>
{% endif %}
