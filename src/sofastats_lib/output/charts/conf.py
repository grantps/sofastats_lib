DOJO_CHART_JS = """\
<script type="text/javascript">

function getAllFunctions(){
    var allFunctions = [];
    for (var i in window) {
      if((typeof window[i]).toString()=="function"){
        fn_name = window[i].name;
        if (fn_name.startsWith('make_chart')) {
            allFunctions.push(fn_name);
        }
      }
   }
   return allFunctions;
}

makeObjects = function(){
    functions = getAllFunctions();
    functions.forEach(fn_name => window[fn_name]());
};
dojo.addOnLoad(makeObjects);

var DEFAULT_SATURATION  = 100,
DEFAULT_LUMINOSITY1 = 75,
DEFAULT_LUMINOSITY2 = 50,

c = dojox.color,

cc = function(colour){
    return function(){ return colour; };
},

hl = function(colour){

    var a = new c.Color(colour),
        x = a.toHsl();
    if(x.s == 0){
        x.l = x.l < 50 ? 100 : 0;
    }else{
        x.s = DEFAULT_SATURATION;
        if(x.l < DEFAULT_LUMINOSITY2){
            x.l = DEFAULT_LUMINOSITY1;
        }else if(x.l > DEFAULT_LUMINOSITY1){
            x.l = DEFAULT_LUMINOSITY2;
        }else{
            x.l = x.l - DEFAULT_LUMINOSITY2 > DEFAULT_LUMINOSITY1 - x.l
                ? DEFAULT_LUMINOSITY2 : DEFAULT_LUMINOSITY1;
        }
    }
    return c.fromHsl(x);
}

getfainthex = function(hexcolour){
    var a = new c.Color(hexcolour)
    x = a.toHsl();
    x.s = x.s * 1.5;
    x.l = x.l * 1.25;
    return c.fromHsl(x);
}

makefaint = function(colour){
    var fainthex = getfainthex(colour.toHex());
    return new dojox.color.Color(fainthex);
}

</script>
"""
