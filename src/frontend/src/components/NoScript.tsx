export default function NoScript() {
  return <noscript>
    <div className="medium-center">
      <div className="panel alert alert-warning">
        <button className="close-button" aria-label="Close alert" >
          <i className="fa-solid fa-xmark"></i>
        </button>
        <h2>Warning</h2>
        <div className="panel-inset mb0">
          JavaScript is required for logging in and making changes to your servers.
        </div>
      </div>
    </div>
  </noscript>
}
