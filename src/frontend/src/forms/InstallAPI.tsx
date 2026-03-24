import { useState, FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { apiClient, APIError } from "../api/client";
import { SubmitButton } from "./SubmitButton";
import { validateForm, serverName, serverVersion } from "../utils/validation";

export default function InstallFormAPI() {
  const { name } = useParams();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    name: name || "",
    version: "1.1.0",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [serverError, setServerError] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setServerError("");

    // Client-side validation
    const validationErrors = validateForm(formData, {
      name: serverName(),
      version: serverVersion(),
    });

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setErrors({});
    setIsSubmitting(true);

    try {
      await apiClient.createServer(formData.name, formData.version);
      navigate(`/servers/${formData.name}/`);
    } catch (error) {
      if (error instanceof APIError) {
        if (error.status === 429) {
          const retryAfter = error.data?.retry_after || 30;
          setServerError(`Server creation is on cooldown. Please wait ${retryAfter} seconds.`);
        } else {
          setServerError(error.message);
        }
      } else {
        setServerError("Failed to create server");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="name">Server Name</label>
        <input
          id="name"
          name="name"
          type="text"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          placeholder="my-server"
          required
        />
        {errors.name && <p style={{ color: "red", fontSize: "0.875rem" }}>{errors.name}</p>}
      </div>

      <div>
        <label htmlFor="version">Factorio Version</label>
        <input
          id="version"
          name="version"
          type="text"
          value={formData.version}
          onChange={(e) => setFormData({ ...formData, version: e.target.value })}
          placeholder="1.1.0"
          required
        />
        {errors.version && <p style={{ color: "red", fontSize: "0.875rem" }}>{errors.version}</p>}
        <p style={{ fontSize: "0.875rem", color: "#666" }}>
          Format: X.Y.Z (e.g., 1.1.0, 1.1.110, 2.0.0)
        </p>
      </div>

      {serverError && <p style={{ color: "red" }}>{serverError}</p>}

      <SubmitButton disabled={isSubmitting} />
    </form>
  );
}
