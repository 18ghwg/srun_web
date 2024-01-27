
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
        var qrc_img_url =  $('#qrc_img').attr('src');  //二维码地址
        var img_div=document.getElementById("log_img");  // 图片框
        const kami = $("#kami").val();
        const kami_input = document.getElementById("kami-div");  // 卡密输入框
        if (kami_input.style.display !== "none") {
            if (kami === "") {
                alert("未输入卡密");
            }
        }
        $.ajax({
            url: '/code/qrc/check_login',
            method: 'POST',
            data: {"qrc_img_url": qrc_img_url, "kami": kami},
            success: function(res){
                document.getElementById('qrc_info').className = "collapse.in";  // 常显
                document.getElementById("qrc_res").innerHTML= "正在提交..."
                img_div.style.display="none";  // 隐藏二维码
                //对html传值
                if (res.code === 200){
                    document.getElementById("qrc_res").innerHTML="获取到IMECode！已自动填写！";

                }else if (res.code === 400){  // 非赞助用户
                    kami_input.style.display = "block";  // 显示卡密输入框
                    document.getElementById("qrc_res").innerHTML=res.msg;


                }else if (res.code === 300){
                    document.getElementById("qrc_res").innerHTML="跑步结果：运行失败！";
                }else{
                    document.getElementById("qrc_res").innerHTML="未登录！";
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


//等待网页加载完成后执行
$(function () {
    check_login();  // 检测登录状态
    get_login_img();  // 获取登录二维码
})