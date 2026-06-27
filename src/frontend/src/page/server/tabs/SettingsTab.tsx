import ManageServerForm, { type ManageServerData } from "@/forms/Settings";

interface Props {
  name: string;
  data: ManageServerData;
}

export default function SettingsTab({ name, data }: Props) {
  return (
    <div className="panel-inset-lighter">
      <h3 className="mt0">Server Settings</h3>
      <ManageServerForm name={name} data={data} />
    </div>
  );
}
