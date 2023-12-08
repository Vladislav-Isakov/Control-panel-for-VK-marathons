function GetCommentThread(group_id, post_id, comment_id, button_id, collapse) {
    $.ajax({
      type: "GET",
      url: '/post_comment_thread',
      data: {'group_id': group_id, 'post_id': post_id, 'comment_id': comment_id},
      beforeSend: function () {
        $('#' + button_id).html('<span class="spinner-grow spinner-grow-sm text-primary" role="status" aria-hidden="true"></span>Загружаю ветку комментария...');
      },
      success: function (response) {
        setTimeout(function() {
          $('#' + button_id).html('Ветка комментария');
        }, 500);
        $('#' + collapse).html(response);
      },
      error: function (error_msg) {
        // Вывод текста ошибки отправки
        $('#' + button_id).html('<span class="spinner-grow spinner-grow-sm text-danger" role="status" aria-hidden="true"></span>Ошибка загрузки ветки');
        setTimeout(function() {
          $('#' + button_id).html('Ветка комментария');
        }, 2500);
      }
    });
    return false;
}

function GetComments(group_id, post_id, page) {
    var button_id = '#button_get_comments_' + post_id;
    $.ajax({
        type: "GET",
        url: '/post_comments',
        data: {'group_id': group_id, 'post_id': post_id, 'page': page},
        beforeSend: function () {
            $(button_id).html('<span class="spinner-grow spinner-grow-sm text-primary" role="status" aria-hidden="true"></span>Загружаю комментарии...');
        },
        success: function (response) {
            setTimeout(function() {
                $(button_id).html('Комментарии');
            }, 500);
            $('#comments_under_the_post_' + post_id).html(response);
        },
        error: function (error_msg) {
            // Вывод текста ошибки отправки
            $(button_id).html('<span class="spinner-grow spinner-grow-sm text-danger" role="status" aria-hidden="true"></span>Ошибка загрузки комментариев');
            setTimeout(function() {
                $(button_id).html('Комментарии');
            }, 2500);
        }
    });
    return false;
}
function GetTasksByCategory(group_id, category, button){
    if (group_id == ''){
        return;
    }
    if (category == ''){
        return;
    }
    if (button == ''){
        return;
    }
    $.ajax({
        type: "GET",
        url: '/tasks_by_category',
        data: {'group_id': group_id, 'category': category},
        beforeSend: function () {
            $(button).html('<span class="spinner-grow spinner-grow-sm text-primary" role="status" aria-hidden="true"></span>Загрузка списка...');
        },
        success: function (response) {
            $(button).html('<span class="spinner-grow spinner-grow-sm text-primary" role="status" aria-hidden="true"></span>Список загружен');
            setTimeout(function() {
                $("#tasks_by_category").html(response);
            }, 1500);
        },
        error: function () {
            $(button).html('<span class="spinner-grow spinner-grow-sm text-danger" role="status" aria-hidden="true"></span>Ошибка загрузки');
        }
    });
    return false;
}