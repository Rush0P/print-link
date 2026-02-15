function calculatePrice() {
    var type = document.getElementById("print_type").value;
    var pages = document.getElementById("pages").value;

    var price = 0;

    if(type == "bw"){
        price = 5;
    } else {
        price = 10;
    }

    var total = price * pages;

    document.getElementById("total").innerText = total;
}