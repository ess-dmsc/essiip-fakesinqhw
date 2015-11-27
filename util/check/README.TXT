listsobj motor { klass { detector}}
listsobj motor {-not klass { detector}}
listsobj motor { type {-not @any}}
listsobj motor { type @any}
listsobj motor { control false   type @any}
listsobj motor {    type @missing}
listsobj motor { control false   type @missing}
listsobj motor { data true   type {part instrument nxvgroup}}
listsobj motor { data true sicsdev @any  type {part instrument nxvgroup}}
listsobj motor {-not data true sicsdev @any  type {part instrument nxvgroup}}
listsobj motor {-not mutable {true false} privilege {spy user manager read_only internal} kind {command event hobj ilist script} drivable {true false} countable {true false} callback {true false} environment {true false} nxalias {text} units {alpha}}
listsobj motor {mutable {true false} }
listsobj motor {mutable {a true} }
listsobj sicsvariable {control false data false}
listnode / {sicsdev ::histogram_memory::y_pixel_offset}
listnode / {sicsdev ::histogram_memory::}
listnode / {sicsdev ::histogram_memory::*}
listnode / {sicsdev @any}
listnode / {control true type {command}}
listnode / {type {command}}
listnode / {type {-not command}}
listnode / {type {part instrument nxvgroup commandset}}
listnode / { data false   type {part instrument nxvgroup}}
listnode / { data true sicsdev @any  type {part instrument nxvgroup}}
listnode / {-not klass command}
listnode / { control false   type @missing}
listnode / { data true   type {part}}
listnode / {-not data true sicsdev @any  type {part instrument nxvgroup}}
listnode /instrument/sample {-not mutable {true false} privilege {spy user manager read_only internal} kind {command event hobj ilist script} drivable {true false} countable {true false} callback {true false} environment {true false} nxalias {text} units {alpha}}
listnode / {data true sicsdev @any  type @any}

# To find which node the hmm has been added under do
listnode / {sicsdev hmm}
