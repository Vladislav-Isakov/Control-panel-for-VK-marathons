function ClickButtonListUsersWithRights(button_id) {
    let button = document.getElementById(button_id)
    $.ajax({
        url: "/users_with_rights",
        type: "get",
        dataType: "html",
        beforeSend: function () {
        button.innerHTML = '<span class="spinner-grow spinner-grow-sm text-primary" role="status" aria-hidden="true"></span>Обновление...';
        },
        success: function(response) {
        if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
            $('#main-menu-phone').offcanvas('hide');
        }
        $("#base_main").html(response);
        setTimeout(function() {
            button.innerHTML = 'Пользователи с правами';
        }, 2500);
        },
        error: function(response) {
        button.innerHTML = '<span class="spinner-grow spinner-grow-sm text-danger" role="status" aria-hidden="true"></span>Ошибка обновления';
        setTimeout(function() {
            button.innerHTML = 'Пользователи с правами';
        }, 2500);
        }
    });
    return false;
}

function ClickButtonListMarathonGroups(button_id) {
    let button = document.getElementById(button_id)
    $.ajax({
        url: "/marathon_groups",
        type: "get",
        dataType: "html",
        beforeSend: function () {
        button.innerHTML = '<span class="spinner-grow spinner-grow-sm text-primary" role="status" aria-hidden="true"></span>Обновление...';
        },
        success: function(response) {
        if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
            $('#main-menu-phone').offcanvas('hide');
        }
        $("#base_main").html(response);
        setTimeout(function() {
            button.innerHTML = 'Список групп';
        }, 2500);
        },
        error: function() {
        button.innerHTML = '<span class="spinner-grow spinner-grow-sm text-danger" role="status" aria-hidden="true"></span>Ошибка обновления';
        setTimeout(function() {
            button.innerHTML = 'Список групп';
        }, 2500);
        }
    });
    return false;
}
function ClickButtonListCuratorsInGroups(button_id) {
    let button = document.getElementById(button_id)
    $.ajax({
        url: "/curators_in_marathon_groups",
        type: "get",
        dataType: "html",
        beforeSend: function () {
        button.innerHTML = '<span class="spinner-grow spinner-grow-sm text-primary" role="status" aria-hidden="true"></span>Обновление...';
        },
        success: function(response) {
        if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
            $('#main-menu-phone').offcanvas('hide');
        }
        $("#base_main").html(response);
        setTimeout(function() {
            button.innerHTML = 'Кураторы в группах';
        }, 2500);
        },
        error: function() {
        button.innerHTML = '<span class="spinner-grow spinner-grow-sm text-danger" role="status" aria-hidden="true"></span>Ошибка обновления';
        setTimeout(function() {
            button.innerHTML = 'Кураторы в группах';
        }, 2500);
        }
    });
    return false;
}
function ClickButtonListGoogleInPanel(button_id) {
    let button = document.getElementById(button_id)
    $.ajax({
        url: "/tables_in_the_panel",
        type: "get",
        dataType: "html",
        beforeSend: function () {
        button.innerHTML = '<span class="spinner-grow spinner-grow-sm text-primary" role="status" aria-hidden="true"></span>Обновление...';
        },
        success: function(response) {
        if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
            $('#main-menu-phone').offcanvas('hide');
        }
        $("#base_main").html(response);
        setTimeout(function() {
            button.innerHTML = 'Список таблиц';
        }, 2500);
        },
        error: function() {
        button.innerHTML = '<span class="spinner-grow spinner-grow-sm text-danger" role="status" aria-hidden="true"></span>Ошибка обновления';
        setTimeout(function() {
            button.innerHTML = 'Список таблиц';
        }, 2500);
        }
    });
    return false;
}
function ClickButtonListCuratorGroups(button_id) {
    let button = document.getElementById(button_id)
    $.ajax({
        url: "/curator_groups",
        type: "get",
        dataType: "html",
        beforeSend: function () {
        button.innerHTML = '<span class="spinner-grow spinner-grow-sm text-primary" role="status" aria-hidden="true"></span>Обновление...';
        },
        success: function(response) {
        if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
            $('#main-menu-phone').offcanvas('hide');
        }
        $("#base_main").html(response);
        setTimeout(function() {
            button.innerHTML = 'Мои группы';
        }, 2500);
        },
        error: function() {
        button.innerHTML = '<span class="spinner-grow spinner-grow-sm text-danger" role="status" aria-hidden="true"></span>Ошибка обновления';
        setTimeout(function() {
            button.innerHTML = 'Мои группы';
        }, 2500);
        }
    });
    return false;
}
function ClickButtonListUsersWithAccessInPanel(button_id) {
    let button = document.getElementById(button_id)
    $.ajax({
    url: "/users_have_access_to_the_panel",
    type: "get",
    dataType: "html",
    beforeSend: function () {
        button.innerHTML = '<span class="spinner-grow spinner-grow-sm text-primary" role="status" aria-hidden="true"></span>Обновление...';
    },
    success: function(response) {
        if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
        $('#main-menu-phone').offcanvas('hide');
        }
        $("#base_main").html(response);
        setTimeout(function() {
        button.innerHTML = 'Список пользователей';
        }, 2500);
    },
    error: function() {
        button.innerHTML = '<span class="spinner-grow spinner-grow-sm text-danger" role="status" aria-hidden="true"></span>Ошибка обновления';
        setTimeout(function() {
        button.innerHTML = 'Список пользователей';
        }, 2500);
    }
    });
    return false;
}

function ClickButtonListUsersWithRequestedAccessInPanel(button_id) {
    let button = document.getElementById(button_id)
    $.ajax({
    url: "/users_with_requested_access_to_the_panel",
    type: "get",
    dataType: "html",
    beforeSend: function () {
        button.innerHTML = '<span class="spinner-grow spinner-grow-sm text-primary" role="status" aria-hidden="true"></span>Обновление...';
    },
    success: function(response) {
        if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
        $('#main-menu-phone').offcanvas('hide');
        }
        $("#base_main").html(response);
        setTimeout(function() {
        button.innerHTML = 'Запросы доступа';
        }, 2500);
    },
    error: function() {
        button.innerHTML = '<span class="spinner-grow spinner-grow-sm text-danger" role="status" aria-hidden="true"></span>Ошибка обновления';
        setTimeout(function() {
        button.innerHTML = 'Запросы доступа';
        }, 2500);
    }
    });
    return false;
}