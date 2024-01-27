$('#submit').click(function () {

    if (!$('#check').prop('checked')) {
        layer.tips('请勾选并同意使用协议', '#check', {
            tips: [1, '#FF3366'],
        });
        return false;
    }
    ;
    var token = $('#token').val();
    var beizhu = $('#beizhu').val();
    var email = $('#email').val();
    if (email == '') {
        $('#email').focus();
        layer.tips('请填写QQ邮箱', '#email', {
            tips: [1, '#FF3366'],
        });
        return false;
    } else if (email.search('@') === -1) {  //字符长度判断
        $('#email').focus();
        layer.tips('请填写完整邮箱，以便token失效通知！', '#email', {
            tips: [1, '#FF3366'],
        });
        return false;
    } else if (token == '') {
        $('#token').focus();
        layer.tips('请填你抓到的Token', '#token', {
            tips: [1, '#FF3366'],
        });
        return false;
    } else if (token.search('=') !== -1) {  //token判断
        $('#token').focus();
        layer.tips('请截取等于号后面的32位字符', '#token', {
            tips: [1, '#FF3366'],
        });
        return false;
    } else if ((token.length) !== 32) {  //字符长度判断
        $('#token').focus();
        layer.tips('Token长度应为32位的字符！', '#token', {
            tips: [1, '#FF3366'],
        });
        return false;
    } else if (beizhu == '') {
        $('#beizhu').focus();
        layer.tips('请填写你的昵称', '#beizhu', {
            tips: [1, '#FF3366'],
        });
        return false;
    }
});
