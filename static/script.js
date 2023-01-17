// onclick for .btn-select

$('.btn-select').on('click', function() {
    var $this = $(this);
    $this.toggleClass('active');
    console.log($this.attr('id'));
    if ($this.hasClass('active')) {
        $this.text('✓ ' + $this.text());
        $('input[name=' + $this.attr('id') + ']').val("true");
    } else {
        $this.text($this.text().replace('✓ ', ''));
        $('input[name=' + $this.attr('id') + ']').val("false");
    }
});

$('#selectpage').on('click', function() {
    var $this = $(this);
    $this.toggleClass('active');
    if ($this.hasClass('active')) {
        $('#type').val("selected");
        $("#query").hide();
        $("#select").show();
        $("#select").css("height", "500px");
        // set iframe src
        var url = $("#query").val()
        fetch("/dumpurl?url=" + url)
        .then((response) => response.json())
        .then((data) => {
            console.log(data);
            $("#preview").contents().find("html").html(data);
        });
    } else {
        $('#type').val("query");
        $("#query").show();
        $("#select").css("height", "0px");
        setTimeout(function() {
            $("#select").hide();
        }, 300);
    }
});

$('.accordion h2 span:nth-child(1)').on('click', function() {
    var $this = $(this).parent().parent();
    $this.toggleClass('active');
});

$('.toggle').on('click', function() {
    var $this = $(this);
    if ($this.hasClass('active')) {
        var priv = "private";
    } else {
        var priv = "public";
    }
    fetch("/materials/" + $this.attr('data-uuid') + "/privacy?privacy=" + priv,
    {
        method: 'POST'
    })
    .then((response) => response.json())
    .then((data) => {
        $this.toggleClass('active');
        var priv = data.privacy == "public" ? "Public" : "Private";
        $(".privacy").text(priv);
    });

});

$('#submit-quiz').on('click', function() {
    var $form = $('form#quiz');
    var inputs = $form.find('input');
    var uuid = $form.attr('data-uuid');
    var data = [];
    inputs.each(function() {
        data.push($(this).val());
    });
    console.log(data);
    fetch("/materials/" + uuid + "/quiz", {
        method: 'POST',
        body: JSON.stringify({"answers": data}),
        headers: {
            'Content-Type': 'application/json'
        }, 
    })
    .then((response) => response.json())
    .then((data) => {
        window.location.href = "/materials/" + uuid + "/quiz/attempt/" + data.attemptId;
    });
});

$('#submit-mcq').on('click', function() {
    var $form = $('form#mcq');
    var inputs = $form.find('input:checked');
    var uuid = $form.attr('data-uuid');
    var data = [];
    inputs.each(function() {
        data.push($(this).val());
    });
    console.log(data);
    fetch("/materials/" + uuid + "/mcq", {
        method: 'POST',
        body: JSON.stringify({"answers": data}),
        headers: {
            'Content-Type': 'application/json'
        }, 
    })
    .then((response) => response.json())
    .then((data) => {
        window.location.href = "/materials/" + uuid + "/mcq/attempt/" + data.attemptId;
    });
});

var ttson = false;

$('.tts').on('click', function() {
    if (!ttson) {
        var $this = $(this);
        var material = $this.attr('data-material');
        var uuid = $this.attr('data-uuid');
        var url = "/materials/" + uuid + "/tts/" + material;
        fetch(url)
        .then((response) => response.json())
        .then((data) => {
            var b64tts = data.tts;
            // create audio with base64
            var audio = new Audio('data:audio/mp3;base64,' + b64tts);
            ttson = true;
            audio.play();
            audio.onended = function() {
                ttson = false;
            }
        });
    }
});