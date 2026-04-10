import React, { createContext, useContext, useEffect, useState } from "react";

import type { Version } from "@/types/GameVersion";

interface AvailableVersionContextValue {
	versions: Version[];
	loading: boolean;
	hasError: boolean;
}

const defaultValue: AvailableVersionContextValue = {
	versions: [],
	loading: true,
	hasError: false,
};

const AvailableVersionContext = createContext<AvailableVersionContextValue>(defaultValue);

export function AvailableVersionProvider({ children }: { children: React.ReactNode }) {
	const [versions, setVersions] = useState<Version[]>([]);
	const [loading, setLoading] = useState(true);
	const [hasError, setHasError] = useState(false);

	useEffect(() => {
		(async () => {
			try {
				const res = await fetch("/api/versions", { credentials: "same-origin" });
				if (!res.ok) {
					throw new Error("Failed to fetch versions");
				}

				const data = await res.json();
				if (!Array.isArray(data)) {
					throw new Error("Invalid versions payload");
				}

				const normalizedVersions = data
					.filter((item): item is string => typeof item === "string")
					.map(item => item.trim())
					.filter(Boolean);

				setVersions(normalizedVersions);
				setHasError(false);
			} catch (_err) {
				setVersions([]);
				setHasError(true);
			} finally {
				setLoading(false);
			}
		})();
	}, []);

	return (
		<AvailableVersionContext.Provider value={{ versions, loading, hasError }}>
			{children}
		</AvailableVersionContext.Provider>
	);
}

export function useAvailableVersions() {
	return useContext(AvailableVersionContext);
}

export default AvailableVersionContext;


