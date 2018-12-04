<script>
$(function () {

    // helper function to escape HTML
    var entityMap = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;',
      '/': '&#x2F;',
      '`': '&#x60;',
      '=': '&#x3D;'
    };

    function escapeHtml (string) {
      return String(string).replace(/[&<>"'`=\/]/g, function (s) {
        return entityMap[s];
      });
    }

    var varsFromDjango = {"socket_path": "/otreechat_core/22-telephone_market-421-1-4/127/k1pxxTUYpeXDLn8W2VppJqmHSno/", "channel": "22-telephone_market-421-1-4", "participant_id": 127, "nickname_signed": "Buyer 1:rcmGZeIj4w-gHlEzX9gf6WyrlD8", "nickname_i_see_for_myself": "Buyer 1 (Me)"};
    var channel = varsFromDjango.channel;
    var socketPath = varsFromDjango.socket_path;
    var participantID = varsFromDjango.participant_id;
    var nickname_i_see_for_myself = varsFromDjango.nickname_i_see_for_myself;

    var $chatWidget = $('#_js-otree-chat-' + channel);

    var $messageInput = $chatWidget.find('input');

    var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
    var ws_path = ws_scheme + '://' + window.location.host + socketPath;
    var socket = new ReconnectingWebSocket(ws_path);
    var $msgdiv = $chatWidget.find('.otree-chat__messages');

    // Handle incoming messages
    socket.onmessage = function (message) {

        var messages = JSON.parse(message.data);

        var messagesHTML = '';

        for (var i = 0; i < messages.length; i++) {
            var chatMessage = messages[i];
            var nickname = chatMessage.nickname;


            // need to use ID instead of code, for security
            if (chatMessage.participant_id === participantID) {
                nickname = nickname_i_see_for_myself;
            }

            messagesHTML += "<div class='otree-chat__msg'>" +
                        "<span class='otree-chat__nickname'>" + escapeHtml(nickname) + "</span>" +
                        "<span class='otree-chat__body'>" + escapeHtml(chatMessage.body) + "</span>" +
                        "</div>";

        }
        $msgdiv.append(messagesHTML);
        $msgdiv.scrollTop($msgdiv.prop("scrollHeight"));
    };

    socket.onopen = function () {
        console.log("Connected to chat socket");
        // clear message history so we can re-populate
        $msgdiv.empty();
    };

    function sendMessage() {
        var body = $messageInput.val();

        if (!body) {
            return;
        }

        var data = {
            'body': $messageInput.val(),
            'nickname_signed': varsFromDjango.nickname_signed
        };

        socket.send(JSON.stringify(data));

        $messageInput.val('');
    }

    $chatWidget.find('button').click(function(e) {
        sendMessage();
    });

    // pressing "enter" in the message box should submit a message,
    // NOT the page's form
    $messageInput.on('keypress', function (e) {
        if (e.which == 13) {
            e.preventDefault();
            sendMessage();
        }
    });
});
</script>