export default function CSRF() {
  return <input
    type="hidden"
    name="csrf_token"
    value={(window as any)._csrf_token}
  />
}