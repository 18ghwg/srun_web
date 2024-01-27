
// 检测登录状态
function check_login(){
    $('#check_login').on('click', function(event){
        //定时关闭
        window.setTimeout(function(){
            $(".alert-info").removeClass("show");
        },6000);//显示的时间
        //信息框
        $(".alert-info").addClass("show");
        //对html传值
        document.getElementById("name").innerHTML="检测登录状态中...";
        const qrc_img_url =  $('#qrc_img').attr('src');  //二维码地址
        const img_div = document.getElementById("log_img");  // 图片框
        const input = document.getElementById("token");  //获取input对象
        const qrc_kami = $("#qrc-kami").val();  // qrc卡密
        const data = {"qrc_img_url": qrc_img_url};
        if (qrc_kami !== "") {
            data.kami = qrc_kami
        }
        $.ajax({
            url: '/code/qrc/check_login',
            method: 'POST',
            data: data,
            success: function(res){
                img_div.style.display="none";  // 隐藏二维码
                //对html传值
                if (res.code === 200){
                    $(".alert-info").addClass("show");

                    document.getElementById("name").innerHTML="获取到IMECode！已自动填写！";
                    input.value = res.IMEICode; // 设置token input value

                }else if (res.code === 400){
                    $(".alert-info").addClass("show");
                    document.getElementById("qrc_user_info").style.display = "block";
                    document.getElementById("name").innerHTML="非授权用户！请填购买卡密后进行授权！";
                    document.getElementById("qrc_user_name").innerHTML=res.name;
                    document.getElementById("qrc_user_school").innerHTML=res.school;
                    document.getElementById("qrc_user_userid").innerHTML=res.userid;
                    input.value = "非授权用户，请填购买卡密后进行授权";  // token输入框
                    $('#use-kami').modal('toggle')  // 窗口
                }else{
                    $(".alert-info").addClass("show");
                    document.getElementById("name").innerHTML="未登录！";
                }

            },
            error: function(msg){
                var code = msg.status;
                if(code === 429){
                    document.getElementById("name").innerHTML="频繁请求！";
                }else if(code === 403){
                    document.getElementById("name").innerHTML="erro: 非法请求！";
                }else if(code === 500){
                    document.getElementById("name").innerHTML="erro: 接口请求失败！";
                }
            }

        })
    });
}

// 获取登录二维码
function get_login_img(){
    $('#get_login_img_url, #qrc_login').on('click', function(event){
        //定时关闭
        window.setTimeout(function(){
            $(".alert-info").removeClass("show");
        },3000);//显示的时间
        //信息框
        $(".alert-info").addClass("show");
        //对html传值
        var get_img_button=document.getElementById("qrc_login");  // 获取二维码按钮
        get_img_button.style.display="none";  // 隐藏按钮
        document.getElementById("name").innerHTML="正在获取...";
        $.ajax({
            url: '/code/qrc',
            method: 'POST',
            success: function(res){
                var obj=document.getElementById("log_img");  // 图片框
                obj.style.display="block";  // 显示二维码
                obj.innerHTML='<img id="qrc_img" src="' + res["img_url"] + '" height="180px" width="180px" />'
                if (res['code'] === 200) {
                    document.getElementById("name").innerHTML="获取成功";
                }
                else if(res['code'] === 400){
                    document.getElementById("name").innerHTML="失败！";
                }

            },
            error: function(msg){
                //信息框
                $(".alert-info").addClass("show");
                var code = msg.status;
                if(code === 429){
                    document.getElementById("name").innerHTML="频繁请求！";
                }else if(code === 403){
                    document.getElementById("name").innerHTML="erro: 非法请求！";
                }else if(code === 500){
                    document.getElementById("name").innerHTML="erro: 接口请求失败！";
                }
            }

        })
    });
}

// 兑换卡密
function qrc_use_kami(){
    $('#qrc-use-kami').on('click', function(event) {
        //定时关闭
        window.setTimeout(function(){
            $(".alert-info").removeClass("show");
        },6000);//显示的时间
        document.getElementById("name").innerHTML="正在提交..";
        const name = document.getElementById("qrc_user_name").innerHTML;
        const school = document.getElementById("qrc_user_school").innerHTML;
        const userid = document.getElementById("qrc_user_userid").innerHTML;
        const kami = $("textarea[name='qrc_kami']").val();
        if (kami === "") {
            $(".alert-info").addClass("show");
            document.getElementById("name").innerHTML="卡密不能为空";
        }

        $.ajax({
            url: '/code/qrc/use/kami',
            method: 'POST',
            data:{"name": name, "school": school, "userid": userid, "kami": kami},
            success: function(res){
                $(".alert-info").addClass("show");
                document.getElementById("name").innerHTML=res.msg;
            },
            error: function(msg){
                //信息框
                $(".alert-info").addClass("show");
                var code = msg.status;
                if(code === 429){
                    document.getElementById("name").innerHTML="频繁请求！";
                }else if(code === 403){
                    document.getElementById("name").innerHTML="erro: 非法请求！";
                }else if(code === 500){
                    document.getElementById("name").innerHTML="erro: 接口请求失败！";
                }
            }

        })
    });
}




//等待网页加载完成后执行
$(function () {
    check_login();  // 检测登录状态
    get_login_img();  // 获取登录二维码
    qrc_use_kami(); // 使用扫码卡密
})