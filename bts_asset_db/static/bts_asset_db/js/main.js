$(function()
{
    const vis_records_table = $('#visual_records_table');

    vis_records_table.on("click", "span.visual_note_span", function()
        {
            convert_text_to_input($(this), "visual_note_input").css("color", "black");
        }
    );
    vis_records_table.on("click", "td.visual_note_cell", function()
        {
            if ($(this).children("span").html() === "")
            {
                convert_text_to_input($(this).children("span"), "visual_note_input").css("color", "black");
            }
        }
    );
    vis_records_table.on("blur", "span.visual_note_input", function()
        {
            convert_input_to_text($(this), "visual_note_span").css("color", "white");
            update_notes($(this));
        }
    );

    $('#pat_form').on('submit', function(event)
    {
        event.preventDefault();
        console.log("form submitted!");
        get_records();
    });

    $('#vis_search_form').on('submit', function(event)
    {
        event.preventDefault();
        console.log("form submitted!");
        get_visual_records();
    });

    $('#testModal').on('show.bs.modal', function (event)
    {
        var button = $(event.relatedTarget) // Button that triggered the modal
        var record = button.data('id') // Extract info from data-* attributes
        // If necessary, you could initiate an AJAX request here (and then do the updating in a callback).
        // Update the modal's content. We'll use jQuery here, but you could use a data binding library or other methods instead.
        var modal = $(this)
        modal.find('.modal-title').text('Showing tests for record ID: ' + record)
        get_tests(modal, record)
    })

    $('.list-group-item-bts').on('click', {elem: $(this)}, function(){
        chooseCategory($(this));
    });
});

function demoteCategory({sibling_opacity, time})
{
    $(this).siblings().animate(
        {
            opacity: sibling_opacity
        },
        time,
        function()
        {
            $(this).css("pointer-events", "");
        }
    );

    $(this).animate(
        {
            "top": "0",
            "background-color": "#222"
        },
        time,
        function()
        {
            $(this).removeClass("chosen-category");
        }
    );
}

function promoteCategory({sibling_opacity, time})
{
    const elemOffset = $(this).position().top + $(this).outerHeight();
    $(this).siblings().animate(
        {
            opacity: sibling_opacity
        },
        time,
        function()
        {
            $(this).css("pointer-events", "none");
        }
    );

    $(this).animate(
        {
            "top": "-=" + elemOffset,
            "background-color": "#000"
        },
        time,
        function()
        {
            $(this).addClass("chosen-category");
        }

    );
}

function chooseCategory(elem)
{
    if (elem.hasClass("chosen-category"))
    {
        demoteCategory.call(elem, {sibling_opacity:1, time:500});

        if (elem.parent().data("contains") === "departments")
        {
            const piblings = elem.parent().siblings();

            piblings.children("li[data-department=" + elem.data("department") + "]")
                .fadeOut();

            piblings.children(".chosen-category")
                .each(function(i) {demoteCategory.call($(this), {sibling_opacity:1, time:0})});
        }
        else if (elem.parent().data("contains") === "categories")
        {
            const piblings = elem.parent().siblings("ul[data-contains='subcategories']");

            piblings.children("li[data-category=" + elem.data("category") + "][data-department=" + elem.data("department") + "]")
                .fadeOut();

            piblings.children(".chosen-category")
                .each(function(i) {demoteCategory.call($(this), {sibling_opacity:1, time:0})});
        }

        $("#item_classes_table").fadeOut(500, function(){console.log("Complete!")});
    }
    else
    {
        promoteCategory.call(elem, {sibling_opacity:0, time:500})

        elem.parent("ul[data-contains='departments']")
            .siblings("ul[data-contains='categories']")
            .children("li[data-department=" + elem.attr("data-department") + "]")
            .fadeIn();
        elem.parent("ul[data-contains='categories']")
            .siblings("ul[data-contains='subcategories']")
            .children("li[data-category=" + elem.attr("data-category") + "][data-department=" + elem.attr("data-department") + "]")
            .fadeIn();

        if (elem.parent().data("contains") === "subcategories")
        {
            get_item_classes(elem.data("subcategory"));
            $("#item_classes_table").fadeIn(500, function(){console.log("Complete!")});
        }
    }
}

function update_notes(affected_span)
{
    let visual_id = affected_span.attr('id');
    $.ajax({
        url : visual_id.concat("/note/"),
        type: "POST",
        data:
            {
                new_value : affected_span.html()
            },

        success: function(_)
        {
            console.log("success");
        }
    })
}

function convert_text_to_input(object, new_class)
{
    const content = object.html();
    console.log("Converting the following to input:");
    console.log(content);
    const input = $('<input type="text" />');
    input.val(content);
    object.html(input)
          .attr("class", new_class);
    return object;
}

function convert_input_to_text(object, new_class)
{
    const content = object.children("input").val();
    console.log("Converting the following to text:");
    console.log(content);
    object.html(content)
          .attr("class", new_class);
    return object;
}

function get_item_classes(subcategory)
{
    console.log("get_visual_records is working!");
    $.ajax({
        url : "itemclasses/",
        type: "GET",
        data:
            {
                subcategory : subcategory
            },

        success: function(json)
        {
            console.log(json);
            $("#item_classes_table tbody").html(json.item_classes_rendered);
            console.log("success");
        }
    })
}

function get_visual_records()
{
    console.log("get_visual_records is working!");
    $.ajax({
        url : "search/",
        type: "GET",
        data:
            {
                search_type : $('#id_search_type').val(),
                search_query : $('#id_search_field').val()
            },

        success: function(json)
        {
            console.log(json);
            $("#visual_records_table tbody").html(json.records_rendered);
            console.log("success");
        }
    })
}

function get_records()
{
    console.log("get_records is working!"); // sanity check
    $.ajax({
        url : "records/", // the endpoint
        type : "GET", // http method
        data : {
            search_type : $('#id_search_type').val(),
            search_query : $('#id_search_field').val()
        }, // data sent with the get request

        // handle a successful response
        success : function(json) {
            console.log(json); // log the returned json to the console
            $("#records_table tbody").html(json.records_rendered);
            $("#test_table").html(json.tests_rendered);
            console.log("success"); // another sanity check
        },

        // handle a non-successful response
        // error : function(xhr,errmsg,err) {
        //    $('#results').html("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: "+errmsg+
        //        " <a href='#' class='close'>&times;</a></div>"); // add the error to the dom
        //    console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        // }
    });
}

function get_tests(modal, record_id)
{
    console.log("get_tests is working!"); // sanity check
    $.ajax({
        url : "tests/", // the endpoint
        type : "GET", // http method
        data : {
            record : record_id
        }, // data sent with the get request

        // handle a successful response
        success : function(json) {
            console.log(json); // log the returned json to the console
            modal.find('.modal-body').html(json.tests_rendered);
            console.log("success"); // another sanity check
        },
    });
}

$(function()
{
    // This function gets cookie with a given name
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    var csrftoken = getCookie('csrftoken');

    /*
    The functions below will create a header with csrftoken
    */

    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    function sameOrigin(url) {
        // test that a given url is a same-origin URL
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
                // Send the token to same-origin, relative URLs only.
                // Send the token only if the method warrants CSRF protection
                // Using the CSRFToken value acquired earlier
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
});