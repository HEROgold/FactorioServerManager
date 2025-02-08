
// {% block title %}{{ server.name }}{% endblock %}

// <div class="container-inner">
//     <div id="flashed-messages" class="small-center"></div>
//     {% include "noscript.j2 "%}
//     <div class="medium-center">
//         <div class="panel mb64 pb0 m0 flex-grow flex flex-column">
//             <h2>{{ server.name }}</h2>
//             <a href="{{ url_for('server.delete', name=server.name) }}" onclick="event.preventDefault(); if(confirm('Are you sure?')) { window.location = this.href; }" class="button button-red">
//                 Delete Server
//             </a>
//             <div class="panel-inset-lighter mb12">
//                 <div style="display: flex; align-items: center;">
//                     <h3 style="margin-right: 10px;">Status</h3>
//                     <a style="height: 50%; margin-left: auto;" href="#" onclick="copyToClipboard('{{ server.ip }}:{{ server.port }}')" class="button">Copy {{server.ip}}:{{server.port}}</a>
//                 </div>
//                 <div hx-sse="connect:{{ url_for('server.status', name=server.name) }}">
//                     <h4><strong hx-sse="swap:serverStatusUpdate">{{ server.status }}</strong></h4>
//                 </div>
//                 <br>
//                 <div>
//                     {# TODO: add status things like connected players, running data, playtime, ups, etc. #}
//                     {# https://htmx.org/attributes/hx-sse/ #}
//                     <a hx-post="{{ url_for('server.start', name=server.name) }}" hx-swap="none"
//                         hx-trigger="click throttle:10s" class="button">
//                         Start
//                     </a>
//                     <a hx-post="{{ url_for('server.stop', name=server.name) }}" hx-swap="none"
//                         hx-trigger="click throttle:10s" class="button">
//                         Stop
//                     </a>
//                     <a hx-post="{{ url_for('server.restart', name=server.name) }}" hx-swap="none"
//                         hx-trigger="click throttle:10s" class="button">
//                         Restart
//                     </a>
//                 </div>
//                 <br>
//                 <div class="panel-inset-lighter mb12">
//                     <form method="post" action="{{ url_for('server.update', name=server_name) }}">
//                     <h3>Settings (WIP), not functional yet!</h3>
//                     {{ form.hidden_tag() }}
//                     <table style="width: 100%;">
//                         <tbody>
//                             {% for field in form if field.widget.input_type != "hidden" %}
//                             <tr>
//                                 <td style="padding: 1%;"><strong>{{ field.label }}</strong></td>
//                                 <td style="padding: 1%; width: 90%;">{{ field }}</td>
//                             </tr>
//                             {% endfor %}
//                         </tbody>
//                     </table>
//                     </form>
//                 </div>
//             </div>
//         </div>
//     </div>
// </div>

// <script>
// function copyToClipboard(text) {
//     navigator.clipboard.writeText(text).then(function() {
//         alert('Copied to clipboard');
//     }, function(err) {
//         console.error('Could not copy text: ', err);
//     });
// }
// </script>

import React from "react";

export default function ServerManager() {
    return (
    <>
    
    </>
    );
}