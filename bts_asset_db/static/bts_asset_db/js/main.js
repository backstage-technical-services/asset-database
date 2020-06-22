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

    $('.list-group-container').on('click', '.list-group-item-bts', function(){
        chooseCollection($(this));
    });

    $('#item_container').on('click', '.item-class-bts', function()
    {
        console.log("Itemclass clicked")
        chooseItemclass($(this));
    })

    // $('#item_classes_table').on('click', '.item_class_bts', {elem: $(this)}, function(){
    //     console.log("Itemclass clicked")
    //     get_item_class_info($(this).data("itemclass"));
    // })

    if ($('body').data("page-section") === "asset_db" &&
        $('body').data("page-id") === "search")
    {
        populateDepartments().then(showDepartments());
    }
});

async function chooseCollection(elem)
{
    const data_type = elem.parent().data('contains')

    if (!elem.hasClass('chosen-collection'))
    {
        if (data_type === 'departments')
        {
            promoteCollection(elem)
            await populateCategories(elem.data('id'))
            showCategories()
        }
        else if (data_type === 'categories')
        {
            promoteCollection(elem)
            await populateSubcategories(elem.data('id'))
            showSubcategories()
        }
        else if (data_type === 'subcategories')
        {
            promoteCollection(elem)
            await populateItemclasses(elem.data('id'))
            showItemclasses()
        }
        else
        {
            console.log("Cannot choose collection: invalid data_contains")
        }
    }
    else
    {
        if (data_type === 'departments')
        {
            demoteCollection(elem)
            hideCategories()
        }
        else if (data_type === 'categories')
        {
            demoteCollection(elem)
            hideSubcategories()
        }
        else if (data_type === 'subcategories')
        {
            demoteCollection(elem)
            hideItemclasses()
        }
        else
        {
            console.log("Cannot choose collection: invalid data_contains")
        }
    }
}

function promoteCollection(elem)
{
    // Get offset required to push collection to above top of list
    const elemOffset = elem.position().top + elem.outerHeight();

    // Fade out other collections over 500ms
    // After this, ignore pointer events
    // Asynchronous
    hideElement(elem.siblings());

    // Push collection to above top of list over 500ms and fade background to black
    // Add chosen-collection class
    // Asynchronous
    elem.animate(
        {
            "top": "-=" + elemOffset,
            "background-color": "#000"
        },
        500,
        function()
        {
            elem.addClass("chosen-collection");
        }
    );
}

function demoteCollection(elem)
{
    // Fade in other collections over 500ms
    // After this, enable pointer events
    // Asynchronous
    showElement(elem.siblings())

    // Push collection to above top of list over 500ms and fade background to black
    // Add chosen-category class
    // Asynchronous
    elem.animate(
        {
            "top": 0,
            "background-color": "#222"
        },
        500,
        function()
        {
            elem.removeClass("chosen-collection");
        }
    );
}

function fillWithCollections(parent_list, collections, name_of_collection)
{
    parent_list.empty();

    for (const collection of collections)
    {
        let new_collection = document.createElement("li")
        new_collection.className = "list-group-item list-group-item-bts";
        new_collection.dataset.id = collection.pk;
        new_collection.innerText = collection.fields[name_of_collection];

        parent_list.append(new_collection);
    }
}

async function getJSResponseFromEndpoint(endpoint, data)
{
    const params = jQuery.param(data);
    let response = await fetch(endpoint+"?"+params);
    return await response.json();
}

async function populateDepartments()
{
    const department_list = $('ul#department_list')
    const departments = await getJSResponseFromEndpoint('departments/', {});
    fillWithCollections(department_list, departments, "department");
}

async function populateCategories(department_id)
{
    const category_list = $('ul#category_list')
    const categories = await getJSResponseFromEndpoint('categories/', {department_id:department_id});
    fillWithCollections(category_list, categories, "category");
}

async function populateSubcategories(category_id)
{
    const subcategory_list = $('ul#subcategory_list')
    const subcategories = await getJSResponseFromEndpoint('subcategories/', {category_id:category_id});
    fillWithCollections(subcategory_list, subcategories, "subcategory");
}

async function populateItemclasses(subcategory_id)
{
    const itemclass_list = $('div#item_container');
    const itemclasses = await getJSResponseFromEndpoint('itemclasses/', {subcategory_id:subcategory_id});
    generateItemclassTable(itemclass_list, itemclasses);
}

function generateItemclassTable(itemclass_list, itemclasses)
{
    console.log(itemclasses)
    itemclass_list.empty()
    itemclass_list.html(itemclasses.rendered)
}

function showElement(elem)
{
    elem.animate(
        {
            opacity: 1
        },
        500,
        function()
        {
            elem.css("pointer-events", "");
        }
    );
}

function hideElement(elem)
{
    elem.animate(
        {
            opacity: 0
        },
        500,
        function()
        {
            elem.css("pointer-events", "none");
        }
    );
}

function showDepartments()
{
    showElement($('ul#department_list'));
}

function showCategories()
{
    showElement($('ul#category_list'));
}

function showSubcategories()
{
    showElement($('ul#subcategory_list'));
}

function showItemclasses()
{
    showElement($('div#item_container'));
}

function hideCategories()
{
    hideElement($('ul#category_list'));
    hideSubcategories();
}

function hideSubcategories()
{
    hideElement($('ul#subcategory_list'));
    hideItemclasses();
}

async function hideItemclasses()
{
    await hideElement($('div#item_container'));
}

async function chooseItemclass(elem)
{
    const itemclass_id = elem.data('id');
    const formatted_itemclass = await getJSResponseFromEndpoint('itemclasses/' + itemclass_id + '/', {})
    populateItemclass(formatted_itemclass.rendered);
}

function populateItemclass(render)
{
    hideItemclasses();

    $('div#item_container').promise().done(function()
    {
        $('div#item_container').html(render);
        showItemclasses();
    });
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

function get_item_class_info(itemclass)
{
    console.log("get_item_class_info is working with itemclass:"+itemclass);
    $.ajax({
        url: "itemclasses/"+itemclass+"/",
        type: "GET",
        data:
            {
                itemclass: itemclass
            },

        success: function (json) {
            console.log(json);
            $("#item_classes_table_container").fadeOut(500, function() {
                $("#item_classes_table_container").html(json.item_class_rendered);
                console.log("success");
            })

            $("#item_classes_table_container").fadeIn(500, function () {
                console.log("Complete!")
            });
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


// XSRF protection below
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