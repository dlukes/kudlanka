var app = angular.module("mandisApp", []);

app.config(function($interpolateProvider, $locationProvider, $httpProvider) {
  $interpolateProvider.startSymbol('{[');
  $interpolateProvider.endSymbol(']}');
  $locationProvider.html5Mode(true);
  // intercept AJAX errors (connection refused)
  $httpProvider.interceptors.push(function($q) {
    return {
      responseError: function(rejection) {
        if(rejection.status == 0) {
          var mandisApp = $("#mandis-app");
          var scope = angular.element(mandisApp).scope();
          scope.messages = [[
            "danger",
            "Nepodařilo se navázat spojení se serverem."
          ]];
          return null;
        }
        return $q.reject(rejection);
      }
    };
  });
});

app.directive("segProgress", ["$timeout", function ($timeout) {
  return {
    link: function ($scope, element, attrs) {
      $scope.$on("uttManipulated", function () {
        // You might need this timeout to be sure its run after DOM render.
        $timeout(function () {
          $scope.pristine = $("select.ng-pristine").length;
          $scope.dirty = $("select.ng-dirty").length;
          $scope.$apply();
        }, 0, false);
      });
    }
  };
}]);

app.filter("colorTag", function() {
  return function(tag) {
    var $option = $("option:contains(" + tag + ")");
    if (tag.match(/^.{2}[IMY]/)) {
      $option.addClass("text-info");
    } else if (tag.match(/^.{2}F/)) {
      $option.addClass("text-danger");
    } else if (tag.match(/^.{2}N/)) {
      $option.addClass("text-warning");
    }
    return tag;
  };
});

app.controller("mandisCtrl", function($scope, $http, $location) {
  var api = "api";
  var sonda, prev, next;

  // get utterance from API either by sid or by "random" assignment (as
  // specified by API call in request)
  function getUtt(request) {
    // if we're being passed an object, it's an event object (onpopstate or
    // onload) → ditch it
    if (typeof(request) === "object") {
      var sid = $location.path().split("/");
      // flask ensures a trailing slash, so the sid is always second to last
      // when splitting on "/":
      sid = sid[sid.length - 2];
      request = sid == "edit" ? "/assign/" : "/sid/" + sid + "/";
    }
    $http.get(api + request).
      success(function(data) {
        $scope.messages = data.messages;
        $scope.num = data.num;
        $scope.utt = data.utt;
        $scope.uttManipulated();
        $scope.sid = data.sid;
        $scope.user = data.user;
        var sonda_index = data.sid.split("_");
        sonda = sonda_index[0];
        prev = next = parseInt(sonda_index[1]);
        $scope.prev = [];
        $scope.next = [];
        $scope.helpTag = "";
        $location.path("/edit/" + data.sid + "/");
      }).
      error(function(data) {
        $scope.messages = data.messages;
        $scope.user = data.user;
      });
  }

  $scope.getPrev = function() {
    $http.get(api + "/sid/" + sonda + "_" + --prev + "/").
      success(function(data) {
        $scope.prev.unshift({utt: data.utt, num: data.num});
        $scope.messages = data.messages;
      }).
      error(function(data) {
        $scope.messages = data.messages;
      });
  };

  $scope.getNext = function() {
    $http.get(api + "/sid/" + sonda + "_" + ++next + "/").
      success(function(data) {
        $scope.next.push({utt: data.utt, num: data.num});
        $scope.messages = data.messages;
      }).
      error(function(data) {
        $scope.messages = data.messages;
      });
  };

  $scope.submitUtt = function() {
    $http.post(api + "/sid/" + $scope.sid + "/", $scope.utt).
      success(function(data) {
        $scope.messages = null;
        $scope.disambForm.$setPristine();
        getUtt("/assign/");
      }).
      error(function(data) {
        $scope.messages = data.messages;
        $scope.user = data.user;
      });
  };

  $scope.firstKey = function(obj) {
    if (obj !== null && typeof obj == "object") {
      for (var k in obj) return k;
    } else {
      return undefined;
    }
  };

  $scope.numOfKeys = function(obj) {
    if (obj !== null && typeof obj == "object") {
      return Object.keys(obj).length;
    } else {
      return undefined;
    }
  };

  $scope.postag = [
      {
        label: "Slovní druh",
        "N": "substantivum (podstatné jméno)",
        "A": "adjektivum (přídavné jméno)",
        "P": "pronomen (zájmeno)",
        "C": "numerál (číslovka, nebo číselný výraz s číslicemi)",
        "V": "verbum (sloveso)",
        "D": "adverbium (příslovce)",
        "R": "prepozice (předložka)",
        "J": "konjunkce (spojka)",
        "T": "partikule (částice)",
        "I": "interjekce (citoslovce)",
        "X": "neznámý, neurčený, neurčitelný slovní druh",
        "Z": "interpunkce, hranice věty"
      },
      {
        label: "Detailní určení slovního druhu",
        "!": "zkratka jako adverbium",
        "*": "slovo „krát“ (slovní druh: spojka)",
        ",": "spojka podřadicí (vč. „aby“ a „kdyby“ ve všech tvarech)",
        ".": "zkratka jako adjektivum",
        ":": "interpunkce všeobecně",
        ";": "zkratka jako substantivum",
        "=": "číslo psané číslicemi (značkováno jako slovní druh: číslovka -"
          + " 'C')",
        "?": "číslovka „kolik“",
        "^": "spojka souřadicí",
        "}": "číslovka psaná římskými číslicemi",
        "~": "zkratka jako sloveso",
        "@": "morfologickou analýzou nerozpoznaný tvar (slovní druh: 'X' ="
          + " neznámý)",
        "0": "předložka s připojeným „-ň“ (něj), „proň“, „naň“,"
          + " atd. (značkováno jako slovní druh: zájmeno - 'P')",
        "1": "vztažné přivlastňovací zájmeno „jehož“, „jejíž“, …",
        "2": "slovo před pomlčkou",
        "3": "zkratka jako číslovka",
        "4": "vztažné nebo tázací zájmeno s adjektivním skloňováním (obou typů:"
          + " „jaký“, „který“, „čí“, …)",
        "5": "zájmeno „on“ ve tvarech po předložce (tj. „n-“: „něj“, „něho“,"
          + " …)",
        "6": "reflexívní zájmeno „se“ v dlouhých tvarech („sebe“, „sobě“,"
          + " „sebou“)",
        "7": "reflexívní zájmeno „se“, „si“ pouze v těchto tvarech, a dále"
          + " „ses“, „sis“",
        "8": "přivlastňovací zájmeno „svůj“",
        "9": "vztažné zájmeno „jenž“, „již“, … po předložce („n-“: „něhož“,"
          + " „níž“, …)",
        "A": "adjektivum obyčejné",
        "B": "sloveso, tvar přítomného nebo budoucího času",
        "C": "adjektivum, jmenný tvar",
        "D": "zájmeno ukazovací („ten“, „onen“, …)",
        "E": "vztažné zájmeno „což“",
        "F": "součást předložky, která nikdy nestojí samostatně („nehledě“,"
          + " „vzhledem“, …)",
        "G": "přídavné jméno odvozené od slovesného tvaru přítomného"
          + " přechodníku",
        "H": "krátké tvary osobních zájmen („mě“, „mi“, „ti“, „mu“, …)",
        "I": "citoslovce (značkováno jako slovní druh: citoslovce - 'I')",
        "J": "vztažné zájmeno „jenž“ („již“, …), bez předložky",
        "K": "zájmeno tázací nebo vztažné „kdo“, vč. tvarů s „-ž“ a „-s“",
        "L": "zájmeno neurčité „všechen“, „sám“",
        "M": "přídavné jméno odvozené od slovesného tvaru minulého"
          + " přechodníku",
        "N": "substantivum, obyčejné",
        "O": "samostatně stojící zájmena „svůj“, „nesvůj“, „tentam“",
        "P": "osobní zájmena (vč. tvaru „tys“)",
        "Q": "zájmeno tázací/vztažné „co“, „copak“, „cožpak“",
        "R": "předložka, obyčejná",
        "S": "zájmeno přivlastňovací „můj“, „tvůj“, „jeho“ (vč. plurálu)",
        "T": "částice (slovní druh 'T')",
        "U": "adjektivum přivlastňovací (na „-ův“ i „-in“)",
        "V": "předložka vokalizovaná („ve“, „pode“, „ku“, …)",
        "W": "zájmena záporná („nic“, „nikdo“, „nijaký“, „žádný“, …)",
        "X": "slovní tvar, který byl rozpoznán, ale značka (ve slovníku)"
          + " chybí",
        "Y": "zájmeno „co“ spojené s předložkou („oč“, „nač“, „zač“)",
        "Z": "zájmeno neurčité („nějaký“, „některý“, „číkoli“, „cosi“, …)",
        "a": "číslovka neurčitá („mnoho“, „málo“, „tolik“, „několik“,"
          + " „kdovíkolik“, …)",
        "b": "příslovce (bez určení stupně a negace; „pozadu“, „naplocho“, …)",
        "c": "kondicionál slovesa být („by“, „bych“, „bys“, „bychom“,"
          + " „byste“)",
        "d": "číslovka druhová, adjektivní skloňování („jedny“, „dvojí“,"
          + " „desaterý“, …)",
        "e": "slovesný tvar přechodníku přítomného („-e“, „-íc“, „-íce“)",
        "f": "slovesný tvar: infinitiv",
        "g": "příslovce (s určením stupně a negace; „velký“, „zajímavý“, …)",
        "h": "číslovky druhové „jedny“ a „nejedny“",
        "i": "slovesný tvar rozkazovacího způsobu",
        "j": "číslovka druhová >= 4, substantivní postavení („čtvero“,"
          + " „desatero“, …)",
        "k": "číslovka druhová >= 4, adjektivní postavení, krátký tvar"
          + " („čtvery“, …)",
        "l": "číslovky základní 1-4, „půl“, …; sto a tisíc v nesubstantivním"
          + " skloňování",
        "m": "slovesný tvar přechodníku minulého, příp. (zastarale) přechodník"
          + " přítomný dokonavý",
        "n": "číslovky základní >= 5",
        "o": "číslovky násobné neurčité („-krát“: „mnohokrát“, „tolikrát“, …)",
        "p": "slovesné tvary minulého aktivního příčestí (včetně přidaného"
          + " „-s“)",
        "q": "archaické slovesné tvary minulého aktivního příčestí (zakončení"
          + " „-ť“)",
        "r": "číslovky řadové",
        "s": "slovesné tvary pasívního příčestí (vč. přidaného „-s“)",
        "t": "archaické slovesné tvary přítomného a budoucího času (zakončení"
          + " „-ť“)",
        "u": "číslovka tázací násobná „kolikrát“",
        "v": "číslovky násobné („-krát“: „pětkrát“, „poprvé“ …)",
        "w": "číslovky neurčité s adjektivním skloňováním („nejeden“,"
          + " „tolikátý“, „několikátý“ …)",
        "x": "zkratka, slovní druh neurčen/neznámý",
        "y": "zlomky zakončené na „-ina“ (značkováno jako slovní druh: číslovka"
          + " - 'C')",
        "z": "číslovka tázací řadová „kolikátý“"
      },
      {
        label: "Jmenný rod",
        "-": "neurčuje se",
        "F": "femininum (ženský rod)",
        "H": "femininum nebo neutrum (tedy nikoli maskulinum)*",
        "I": "maskulinum inanimatum (rod mužský neživotný)",
        "M": "maskulinum animatum (rod mužský životný)",
        "N": "neutrum (střední rod)",
        "Q": "femininum singuláru nebo neutrum plurálu (pouze u příčestí a"
          + " jmenných adjektiv)*",
        "T": "masculinum inanimatum nebo femininum (jen plurál u příčestí a"
          + " jmenných adjektiv)*",
        "X": "libovolný rod (F/M/I/N)",
        "Y": "masculinum (animatum nebo inanimatum)*",
        "Z": "'nikoli femininum' (tj. M/I/N; především u příslovcí)*"
      },
      {
        label: "Číslo",
        "-": "neurčuje se",
        "D": "duál (pouze 7. pád feminin)",
        "P": "plurál (množné číslo)",
        "S": "singulár (jednotné číslo)",
        "W": "pouze v kombinaci s jmenným rodem 'Q' (singulár pro feminina,"
          + " plurál pro neutra)*",
        "X": "libovolné číslo (P/S/D)"
      },
      {
        label: "Pád",
        "-": "neurčuje se",
        "1": "nominativ (1. pád)",
        "2": "genitiv (2. pád)",
        "3": "dativ (3. pád)",
        "4": "akuzativ (4. pád)",
        "5": "vokativ (5. pád)",
        "6": "lokál (6. pád)",
        "7": "instrumentál (7. pád)",
        "X": "libovolný pád (1/2/3/4/5/6/7)*"
      },
      {
        label: "Přivlastňovací rod",
        "-": "neurčuje se",
        "F": "femininum (ženský rod)",
        "M": "maskulinum animatum (rod mužský životný)",
        "X": "libovolný rod (F/M/I/N)",
        "Z": "'nikoli femininum' (tj. M/I/N; u přivlastňovacích adjektiv)*"
      },
      {
        label: "Přivlastňovací číslo",
        "-": "neurčuje se",
        "P": "plurál (množné číslo)",
        "S": "singulár (jednotné číslo)"
      },
      {
        label: "Osoba",
        "-": "neurčuje se",
        "1": "1. osoba",
        "2": "2. osoba",
        "3": "3. osoba",
        "X": "libovolná osoba (1/2/3)*"
      },
      {
        label: "Čas",
        "-": "neurčuje se",
        "F": "futurum (budoucí čas)",
        "H": "minulost nebo přítomnost (P/R)*",
        "P": "prézens (přítomný čas)",
        "R": "minulý čas",
        "X": "libovolný čas (F/R/P)*"
      },
      {
        label: "Stupeň",
        "-": "neurčuje se",
        "1": "1. stupeň",
        "2": "2. stupeň",
        "3": "3. stupeň"
      },
      {
        label: "Negace",
        "-": "neurčuje se",
        "A": "afirmativ (bez negativní předpony „ne-“)",
        "N": "negace (tvar s negativní předponou „ne-“)"
      },
      {
        label: "Aktivum/pasivum",
        "-": "neurčuje se",
        "A": "aktivum nebo 'nikoli pasívum'",
        "P": "pasívum"
      },
      {
        label: "Nepoužito",
        "-": "neurčuje se"
      },
      {
        label: "Nepoužito",
        "-": "neurčuje se"
      },
      {
        label: "Varianta (stylový příznak)",
        "-": "neurčuje se („základní“ tvar pro kategorie v pozicích 1-14)",
        "1": "varianta, víceméně rovnocenná („méně častá“)",
        "2": "řídká, archaická nebo knižní varianta",
        "3": "velmi archaický tvar, též hovorový",
        "4": "velmi archaický nebo knižní tvar, pouze spisovný (ve své době)",
        "5": "hovorový tvar, ale v zásadě tolerovaný ve veřejných projevech",
        "6": "hovorový tvar (koncovka standardní obecné češtiny)",
        "7": "hovorový tvar (koncovka standardní obecné češtiny), varianta k"
          + " '6'",
        "8": "zkratky",
        "9": "speciální použití (tvary zájmen po předložkách apod.)"
      },
      {
        label: "Vid",
        "-": "neurčuje se",
        "P": "perfektivum (dokonavé sloveso)",
        "I": "imperfektivum (nedokonavé sloveso)",
        "B": "obouvidé sloveso"
      }
    ];

  /* Additional UI behavior */

  // update seg progress
  $scope.uttManipulated = function() {
    $scope.$broadcast("uttManipulated");
  };

  // scroll to top whenever a new message is added
  $scope.$watch("messages", function() {
    window.scrollTo(0, 0);
  });

  // warn the user about losing data if disambForm has been edited
  window.onbeforeunload = function() {
    if ($scope.disambForm.$dirty) {
      return "Pokud opustíte stránku, ztratíte neuloženou práci na aktuálním"
        + " segmentu.";
    } else {
      return null;
    }
  };

  // load the data from the API based on the view requested on each user action
  // (either when page is first loaded, or when history buttons are clicked)
  window.onload = window.onpopstate = getUtt;

});

$(document).ready(function() {
  function adjustHelpTag(e) {
    var $helpTag = $("#help-tag");
    var mediaWidth = Math.max(document.documentElement.clientWidth,
                              window.innerWidth || 0);
    if (mediaWidth >= 992) {
      // fake multi-column layout with fixed position
      var $cont = $("#main-ui");
      var cWidth = $cont.outerWidth();
      var cMargin = parseInt($cont.offset().left);
      var mediaHeight = Math.max(document.documentElement.clientHeight,
                                 window.innerHeight || 0);
      var footHeight = $("#footer").outerHeight(true);
      var panelTitleHeight = $(".panel-heading").first().outerHeight(true);
      // 71 is the distance from top, 20 is the bottom margin on the panel, and
      // looking at the result, there are still 2 more pixels that need to go
      var maxPanelBodyHeight = mediaHeight - footHeight
            - panelTitleHeight - 71 - 20 - 2;
      $helpTag.outerWidth(.333*cWidth);
      $helpTag.css("right", cMargin);
      $helpTag.find(".panel-body").css("max-height", maxPanelBodyHeight);
    } else {
      // use default responsive stacked layout
      $helpTag.outerWidth("");
      $helpTag.css("right", "");
    }
  }
  $(window).on("resize", adjustHelpTag);
  adjustHelpTag();
});
