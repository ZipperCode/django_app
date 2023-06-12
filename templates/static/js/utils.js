function isChinese(temp) {
    return /^[\u4E00-\u9FA5]+$/.test(temp)
}


function isNull(text){
    return text === undefined || text == "";
}

function isDigit(text){
    return /^[+-]?\d+.?\d*/.test(text)
}
