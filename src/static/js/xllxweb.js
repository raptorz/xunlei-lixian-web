_.templateSettings = {
   interpolate : /\$\{(.+?)\}/g
};

var Login = Backbone.Model.extend({
    urlRoot: "/xunlei/login",
});

var Task = Backbone.Model.extend({
    urlRoot: "/xunlei/task",
    initialize: function () {
        this.on("change:state", this.onStateChange);
        this.on("destroy", this.onRemove);
    },
    onStateChange: function (task, state) {
        var result = render_status(task.id, state);
        var item = $("#t_"+task.id);
        item.children(".item_message").html(result.message);
        item.children(".item_operations").html(result.op);
    },
    onRemove: function (task) {
        var item = $("#t_"+task.id);
        item.remove();
    },
});

var TaskList = Backbone.Collection.extend({
    url: "/xunlei/task",
    model: Task,
    initialize: function () {
        this.bind("reset", this.showView);
    },
    showView: function () {
        var v = new TaskListView({el: $("#body")});
        v.tasklist = this;
        v.render();
    }
});

function render_status(tid, state) {
    var progress_tpl   = _.template($("#progress-tpl").html());
    var completed_tpl  = _.template($("#completed-tpl").html());
    var waiting_tpl    = _.template($("#waiting-tpl").html());
    var downloaded_tpl = _.template($("#downloaded-tpl").html());
    var error_tpl      = _.template($("#error-tpl").html());
    var result = {message:"", op:""};
    switch (state) {
        case 'completed':
            result.op = completed_tpl({id:tid});
            result.message = "离线任务完成";
            break;
        case 'downloading':
            result.op = progress_tpl();
            result.message = "正在离线下载中";
            break;
        case 'working':
            result.op = progress_tpl();
            result.message = "正在下载到本地";
            break;
        case 'waiting':
            result.op = waiting_tpl({id:tid});
            result.message = "本地下载排队中";
            break;
        case 'downloaded':
            result.op = downloaded_tpl({id:tid});
            result.message = "已完成本地下载";
            break;
        case 'error':
            result.op = error_tpl({id:tid});
            result.message = "下载出错请重试";
            break;
        default:
            result.op = progress_tpl();
            result.message = state;
            break;
    };
    return result;
}

var TaskView = Backbone.View.extend({
    initialize: function () {
        this.template = _.template($("#taskitem-tpl").html());
    },
    render: function () {
        var result = render_status(this.task.get('id'), this.task.get('state'));
        this.$el.html(this.template({task:this.task, message:result.message, operations:result.op}));
        return this;
    },
});

var TaskListView = Backbone.View.extend({
    events: {
        'click button.item_cancel'  : 'item_cancel',
        'click button.item_download': 'item_download',
        'click button.item_delete'  : 'item_delete',
        'click button.item_reset'   : 'item_reset',
    },
    render_task: function (task) {
        var v = new TaskView();
        v.task = task;
        this.tbody.append(v.render().$el);
    },
    render: function() {
        var tasklist_tpl = _.template($("#tasklist-tpl").html());
        this.tbody = $("<tbody />");
        this.tasklist.each(this.render_task, this);
        this.$el.html(tasklist_tpl({tasklist:this.tbody.html()}));
        return this;
    },
    item_cancel: function(e) {
        var task = this.tasklist.get($(e.currentTarget).attr('tag'));
        task.save({state:"completed"}, {error: function (task, error) {
            alert(error.statusText);
        }});
    },
    item_download: function(e) {
        var task = this.tasklist.get($(e.currentTarget).attr('tag'));
        task.save({state:"waiting"}, {error: function (task, error) {
            alert(error.statusText);
        }});
    },
    item_delete: function(e) {
        var task = this.tasklist.get($(e.currentTarget).attr('tag'));
        task.destroy({error: function (task, error) {
            alert(error.statusText);
        }});
    },
    item_reset: function(e) {
        var task = this.tasklist.get($(e.currentTarget).attr('tag'));
        var old_state = task.get('state');
        task.save({state:"working"}, {error: function (task, error) {
            alert(error.statusText);
            task.set({state:old_state});
        }});
    }
});

var LoginView = Backbone.View.extend({
    events: {
        'click button#btn_login': 'login'
    },
    initialize: function () {
    },
    render: function () {
        this.$el.html(_.template($("#login-tpl").html(), {}));
    },
    login: function () {
        if ($("#username").val() == "" || $("userpass").val() == "") {
            $("#login_fail").html(_.template($("#login_fail-tpl").html(),
                    {error: "Error", message: "用户名和密码不可为空！"}));
        }
        else {
            var l = new Login;
            l.save({username:$("#username").val(), userpass:$("#userpass").val()},
                {success: function (login) {
                    window.location.href = "#/";
                },
                error: function (login, error) {
                    var msg = "用户名或密码错误！";
                    alert(msg);
                    $("#login_fail").html(_.template($("#login_fail-tpl").html(),
                            {error: error.statusText, message:msg}));
                }
            });
        }
    }
});

var AppRouter = Backbone.Router.extend({
    routes: {
        "": "index",
        "login": "login",
        "logout": "logout",
    },
    index: function() {
        $("#body").html(_.template($("#progress-tpl").html()));
        this.tasklist = new TaskList();
        this.tasklist.fetch({error: function (tasklist, error) {
            if (error.status == 401) {
                window.location.href = "#/login";
            }
            else {
                alert(JSON.stringify(error));
            }
        }});
    },
    logout: function() {
        var l = new Login();
        l.save({username:"-", userpass:"-"});
        window.location.href = "#/";
    },
    login: function() {
        var v = new LoginView({el: $("#body")});
        v.render();
    },
});

$(function () {
    var app = new AppRouter;
    Backbone.history.start();
});
