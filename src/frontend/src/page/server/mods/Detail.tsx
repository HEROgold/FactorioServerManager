import { useState } from "react";
import Card from "@/components/tags/Card";
import Select from "@/components/tags/Select";
import Button from "@/components/tags/Button";
import Placeholder from "@/components/tags/Placeholder";
import Section from "@/components/tags/Section";
import type { DetailResponse, ModRelease } from "./types";

interface Props {
  data: DetailResponse | null;
  loading: boolean;
  onInstall: (modName: string, version: string) => Promise<void> | void;
}

function primaryRelease(releases: ModRelease[]): ModRelease | undefined {
  return releases.find((r) => r.is_recommended) ?? releases[0];
}

export default function Detail({ data, loading, onInstall }: Props) {
  const [selected, setSelected] = useState<string>("");

  if (loading) {
    return <div className="mod-detail-placeholder"><p>Loading mod…</p></div>;
  }
  if (data?.error) {
    return <Placeholder alert>{data.error}</Placeholder>;
  }
  if (!data || !data.mod || !data.mod.name) {
    return (
      <div className="mod-detail-placeholder">
        <h4>No detail available.</h4>
        <p>Select a mod from the search results to preview installable releases.</p>
      </div>
    );
  }

  const { mod, releases, token_missing } = data;
  const recommended = primaryRelease(releases);
  const chosen = selected || recommended?.version || "";

  const handleSubmit = (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (mod.name && chosen) {
      void onInstall(mod.name, chosen);
    }
  };

  return (
    <Card variant="detail">
      <header>
        <div>
          <p className="mod-eyebrow">{mod.category ? mod.category.replace(/\b\w/g, (c) => c.toUpperCase()) : "Mod"}</p>
          <h3>{mod.title || mod.name}</h3>
          <p>{mod.summary}</p>
        </div>
        {mod.thumbnail ? (
          <div className="mod-detail-thumb" role="presentation" style={{ backgroundImage: `url('${mod.thumbnail}')` }} />
        ) : null}
      </header>

      {mod.tags && mod.tags.length > 0 && (
        <div className="mod-detail-tags">
          {mod.tags.map((tag) => (
            <span key={tag} className="mod-pill outline">{tag}</span>
          ))}
        </div>
      )}

      {releases.length > 0 ? (
        <>
          <form className="mod-install-form" onSubmit={handleSubmit}>
            <label>
              <span>Choose release</span>
              <Select name="version" value={chosen} onChange={(e) => setSelected(e.target.value)}>
                {releases.map((release) => (
                  <option key={release.version} value={release.version}>
                    v{release.version} • Factorio {release.factorio_version || "any"} • {release.released_at}
                  </option>
                ))}
              </Select>
            </label>
            <Button className="button" type="submit" disabled={token_missing}>Install to server</Button>
          </form>
          {token_missing && (
            <p className="mod-token-warning">Log in with a Factorio account to download this mod.</p>
          )}
          <div className="mod-release-list">
            {releases.map((release) => (
              <div key={release.version} className={`mod-release-row${release.is_recommended ? " recommended" : ""}`}>
                <strong>v{release.version}</strong>
                <span>Factorio {release.factorio_version || "any"}</span>
                <span>{release.released_at}</span>
                {release.size_label ? <span>{release.size_label}</span> : null}
              </div>
            ))}
          </div>
          {recommended && recommended.dependencies.length > 0 && (
            <Section className="mod-dependencies">
              <h4>Key dependencies</h4>
              <ul>
                {recommended.dependencies.slice(0, 6).map((dep) => (
                  <li key={dep}>{dep}</li>
                ))}
              </ul>
            </Section>
          )}
        </>
      ) : (
        <Placeholder>
          <p>No releases are available for this mod yet.</p>
        </Placeholder>
      )}
    </Card>
  );
}
