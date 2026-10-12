class_name Data
## Story data: areas, memories, and every voice the creature can carry.

const ZONES := [
	{"n": "I", "name": "The Woodpeckers", "place": "Enfield · October 1938", "x0": 0, "x1": 90, "bg": "enfield",
	 "type": "R", "ab": "axe", "noun": "woodcutters in red flannel",
	 "intro": "The Commonwealth has bought the valley. Clearing crews have come for every tree. Take three of them, or go where you like: the Under-Valley runs beneath all three towns.",
	 "done": "The timber jam in the east ridge will give way now. Push into it."},
	{"n": "II", "name": "The Removal", "place": "Greenwich · November 1938", "x0": 90, "x1": 180, "bg": "greenwich",
	 "type": "B", "ab": "shovel", "noun": "grave diggers in brown",
	 "intro": "They are digging up the dead and numbering the boxes. The dead were yours. Take three of the diggers.",
	 "done": "The ridge to Dana has no pass, but the earth before it runs deep. Go down, or take the deep road under the Under-Valley."},
	{"n": "III", "name": "The Line", "place": "Dana · spring 1939", "x0": 180, "x1": 270, "bg": "dana",
	 "type": "K", "ab": "level", "noun": "surveyors in khaki",
	 "intro": "Survey crews are flagging the line where the water will stop. Take three. Learn how they read the ground.",
	 "done": "Read the land near the east ridge. Part of it is not what it appears."},
	{"n": "IV", "name": "The Works", "place": "Winsor Dam · 1939", "x0": 270, "x1": 349, "bg": "works",
	 "type": "E", "ab": "charge", "noun": "engineers in blue",
	 "intro": "Engineers are closing the valley with earth and concrete. Wardens guard them with rifles. Take three engineers.",
	 "done": "Set a charge against the granite plug in the east ridge. It may take two."},
	{"n": "V", "name": "Many Waters", "place": "The basin · 1939–1946", "x0": 349, "x1": 420, "bg": "basin",
	 "type": "", "ab": "", "noun": "",
	 "intro": "The gates are closed and the river has nowhere to go. The whole valley will fill. Let the water lift you.",
	 "done": ""},
]

const MEMS := {
	"axe": {"title": "The Axe", "from": "learned from the woodpeckers", "quote": "Cut toward the hinge. Let the weight do the work.",
		"how": "You can tear through timber. Push into it. Somewhere behind you, a jam of logs no longer matters."},
	"shovel": {"title": "The Shovel", "from": "learned from the grave crew", "quote": "Go down slow. The earth here is softer than it ought to be.",
		"how": "You can move through soft earth, unseen. The Shaw plot in Enfield had soft ground too."},
	"level": {"title": "The Level", "from": "learned from the surveyors", "quote": "The ground lies. Shoot it twice.",
		"how": "Press F to read the land. False stone shows itself. Remember where you woke."},
	"charge": {"title": "The Charge", "from": "learned from the engineers", "quote": "Granite breaks along its own grain.",
		"how": "Press E beside granite to set a charge. There was granite in the caves under Enfield."},
}

const TYPE_ROW := {"R": 0, "B": 1, "K": 2, "E": 3, "G": 4, "P": 5}
const LABEL := {"R": "the woodcutter", "B": "the grave digger", "K": "the surveyor", "E": "the engineer",
	"G": "the warden", "P": "the townsperson", "D": "the deer", "S": "the sheep"}

const VOICES := {
	"R": [["Amos Haskell, woodcutter", "They pay forty cents an hour to cut down my own father's sugar maples."],
		["Lyman Cooke, woodcutter", "Cut toward the hinge. Let the weight do the work."],
		["Ezra Pratt, woodcutter", "Burn the brush, stack the logs, leave nothing that floats."],
		["Walt Doane, woodcutter", "My boy asked where the birds will go. I told him Belchertown."],
		["Silas Moody, woodcutter", "Every tree in the valley, every last one. They call us the woodpeckers."]],
	"B": [["Hollis Gage, grave crew", "We number the boxes so nobody gets mixed up. Nobody gets mixed up."],
		["Orrin Lamb, grave crew", "Some of the old ones are nothing but a stain and a button."],
		["Dell Fiske, grave crew", "The state pays the families for the moving. Not for the asking."],
		["Rufus Crane, grave crew", "Go down slow. The earth here is softer than it ought to be."],
		["Jonah Wheeler, grave crew", "Whatever is under the Shaw plot, it's warm."]],
	"K": [["Merritt Ames, surveyor", "Flag the line, read the level, don't look at the houses."],
		["C. R. Ballou, surveyor", "Elevation five-thirty. Everything below this line is lake."],
		["Asa Thorne, surveyor", "The ground lies. Shoot it twice."],
		["Ned Kittredge, surveyor", "There are stone walls on the old maps that aren't anywhere you can stand."],
		["Frank Lovell, surveyor", "From the hilltop you can see the whole of it. Four towns in one bowl."]],
	"E": [["Harold Pike, engineer", "Granite breaks along its own grain. You only have to find it."],
		["Theo Bancroft, engineer", "The dam is earth. The core is concrete. The rest is arithmetic."],
		["Gus Ferrante, engineer", "Boston drinks what we build. Boston never asks where it came from."],
		["Lew Mathers, engineer", "Three charges and the hill is gravel."],
		["Ward Esty, engineer", "Four hundred billion gallons, give or take a town."]],
	"G": [["Warden R. Coffin", "Shoot whatever comes up out of that water."],
		["Warden J. Kimball", "I fished this river as a boy. It never had anything this big in it."],
		["Warden L. Hatch", "They told us the valley was empty. The valley is not empty."],
		["Warden E. Bliss", "My mother is buried in Prescott. They never found her box."],
		["Warden P. Shattuck", "Hold the platform till the level's up. Then we can all go home."]],
	"P": [["Marion Haskell, Enfield", "We danced at the town hall until midnight. Then they turned the lights off on us."],
		["Edna Vaughn, Greenwich", "I left the door unlocked. Who would come?"],
		["Earl Shumway, Dana", "Sixty years in one house. They paid me for the house."],
		["Clarence Cooley, Dana", "I'll stay till the water's at my porch. Then I'll stay a little more."]],
}

## Every grave, keyed by the id in data/entities.json.
const DEAD := {
	"thankful": ["Thankful Rich, d. 1851", "I left milk at the spring every night for sixty years. Something always drank it."],
	"hale": ["Prudence Hale, d. 1779", "We named the river Swift. It was never in a hurry."],
	"doane": ["Asa Doane, d. 1868", "Forty years I drove the stage to Palmer. The horses never liked this stretch."],
	"fay_e": ["Silence Fay, d. 1798", "In the drought year we went down under the hill for water. There was always water. There was always something drinking it."],
	"cutler_j": ["Jedediah Cutler, d. 1812", "We cut ice from the river in January. Some winters it was warm underneath."],
	"cutler_m": ["Molly Cutler, d. 1814", "Jedediah went through the ice. I hear him in the spring melt."],
	"ward_l": ["Lemuel Ward, town clerk, d. 1897", "Every birth, every death, every deed. The state carried the books away in two trucks."],
	"ward_o": ["Orpha Ward, d. 1903", "The town hall dances were Saturdays. The floor always gave a little in the middle."],
	"stone": ["Josiah Shaw, d. 1822", "Bury us by the house. The church ground is too far from the spring."],
	"shaw": ["Patience Shaw, d. 1830", "We buried ours close to the house, so nothing would be lonely."],
	"gould": ["Isaiah Gould, d. 1859", "From the top of the hill you can count every chimney in four towns."],
	"woods": ["Sarah Woods, d. 1855", "In the cellar the water stands an inch, then two, then goes away again."],
	"sawyer": ["Jotham Sawyer, d. 1872", "Every log we sawed, the blade sang a little flat at the heart."],
	"clough": ["Hannah Clough, d. 1870", "The valley floods every April. It always gives the water back."],
	"rand": ["Rev. Josiah Rand, d. 1817", "The summer it snowed in June, the meetinghouse bell cracked."],
	"pierce": ["Rev. Amos Pierce, d. 1888", "I preached that the meek inherit the earth. No one said which part."],
	"pease": ["Abigail Pease, d. 1863", "My son went south with the regiment and came home in a box."],
	"lyon_b": ["Benjamin Lyon, d. 1880", "Plant the maples so your grandchildren have sugar."],
	"lyon_l": ["Lydia Lyon, d. 1884", "Benjamin planted forty maples. I boiled every drop they gave."],
	"tyler": ["Moses Tyler, d. 1806", "I set every stone in the north wall. It will outlast the town."],
	"eli": ["Eli Stone, sexton, d. 1866", "The north corner sinks every spring. I filled it every fall for thirty years."],
	"child": ["Unnamed child, d. 1937", "There are no words in this one. Only warmth, and the smell of a woodstove."],
	"bartlett": ["Rufus Bartlett, d. 1911", "Fire watch on Pomeroy. I saw lightning walk the valley like a man looking for something."],
	"barlow_i": ["Isaac Barlow, d. 1889", "We built the mill on the river's back, and it let us."],
	"barlow_m": ["Mercy Barlow, d. 1893", "The mill wheel turned all night, even when the race was dry."],
	"ellis_n": ["Nathan Ellis, d. 1936", "Enfield, Dana, Greenwich, Prescott. Say them so they stay."],
	"vaughn": ["Seth Vaughn, miller, d. 1874", "Something in the race took the eels. Took them clean."],
	"alden": ["Ruth Alden, d. 1931", "In the dry summer I heard it under the floorboards. Humming."],
	"clara": ["Clara Thayer, d. 1891", "They burned my heart to stop me coming home. I came home anyway."],
	"lucy": ["Lucy Thayer, d. 1902", "Mother had them dig up Clara. I was next, and no one dug me."],
	"pike": ["John Pike, d. 1898", "I quarried granite for Boston. Boston always comes for the stone."],
	"kittredge": ["Thomas Kittredge, d. 1925", "The river is older than the hills. It remembers being a lake."],
	"works_plot": ["Hezekiah Bliss, d. 1859", "We chose this knoll because it never flooded. Not once in eighty years."],
	"phebe": ["Phebe Ellis, d. 1840", "Prescott was the smallest town. We had the most sky."],
	"fay_z": ["Ezekiel Fay, d. 1801", "Every family here has someone in the ground and no one in the city."],
	"fay_es": ["Esther Fay, d. 1809", "When you go, take us with you. Do not leave us in the dark water alone."],
}

## Named people whose voices are fixed (the rest draw from VOICES by kind).
const NAMED := {
	"marion": ["Marion Haskell, Enfield", "We danced at the town hall until midnight. Then they turned the lights off on us."],
	"ballou": ["C. R. Ballou, surveyor", "Elevation five-thirty. Everything below this line is lake."],
}

## Playable memories. Each opens when its grave is kept or its person is taken.
## A beat may move the walker (`at`, scanning for ground from `row_from`), shows `say`,
## then asks the player to walk to `to` and act, which shows `act`.
const FLASHBACKS := {
	"thankful": {"title": "Thankful Rich", "when": "Enfield · 1794", "row": 5, "dark": 0.72,
		"beats": [
			{"at": 6, "row_from": 1, "say": ["Every night Mother sent me down with the milk.", "\"For the spring,\" she said. \"So it keeps sweet.\""],
				"to": 16, "goal": "Carry the pail to the hollow", "act": ["The hollow went down under the hill. Down and down."]},
			{"at": 26, "row_from": 113, "say": ["The water at the bottom was warm, even in January."],
				"to": 10, "goal": "Set the pail by the spring", "act": ["I set the pail on the stone.", "You were never to look at the water."]},
			{"say": ["Behind me, the pail scraped across the stone."], "to": 24, "goal": "Walk back. Do not look.",
				"act": ["In the morning it was always empty, and always clean."]},
		],
		"end": "Thankful Rich kept the spring for sixty years. She asked to be buried beside it."},
	"eli": {"title": "Eli Stone, sexton", "when": "Greenwich · 1841", "row": 1, "dark": 0.6,
		"beats": [
			{"at": 114, "row_from": 1, "say": ["The north corner of the burying ground sinks every spring."],
				"to": 130, "goal": "Go to the sinking corner", "act": ["Forty barrows of gravel this year. Forty last year."]},
			{"say": ["Then the ground began to hum."], "to": 127, "goal": "Kneel and listen",
				"act": ["Not a sound you hear. A sound your teeth hear.", "Something under the town, turning over in its sleep."]},
			{"say": [], "to": 112, "goal": "Go back to the meetinghouse",
				"act": ["I told the minister it was frost heave. He wrote it down as frost heave."]},
		],
		"end": "Eli Stone filled the north corner every fall for thirty years. It never stopped sinking."},
	"ballou": {"title": "C. R. Ballou, surveyor", "when": "Dana · April 1939", "row": 2, "dark": 0.0,
		"extras": [[2, 252, 1]],
		"beats": [
			{"at": 248, "row_from": 1, "say": ["Elevation five-thirty. Everything below this line is lake.", "Flag the line. Don't look at the houses."],
				"to": 256, "goal": "Set the flag", "act": ["Red flag, white flag. Dana is a line on a map now."]},
			{"say": ["The 1855 map shows a stone wall here, running straight into the hill."], "to": 264, "goal": "Find the wall",
				"act": ["There is no wall. There is the hill.", "I put my hand on it. It was warm, and it gave, like a cheek."]},
		],
		"end": "Ballou wrote \"Ledge. No wall.\" in his book, and moved the line forty feet uphill."},
	"marion": {"title": "Marion Haskell", "when": "Enfield town hall · April 27, 1938", "row": 5, "dark": 0.5,
		"extras": [[5, 51, 1], [0, 52, 1], [5, 54, 1], [1, 55, 1], [5, 56, 1], [3, 59, 1], [3, 60, 1]],
		"beats": [
			{"at": 50, "row_from": 1, "say": ["The Farewell Ball. Everyone from all four towns came.", "The band played until the lights went out."],
				"to": 58, "goal": "Cross the hall to the band", "act": ["They played \"Auld Lang Syne\". We all held hands.", "At midnight the state turned off the power."]},
			{"dark": 0.9, "say": ["In the dark, the floor moved."], "to": 53, "goal": "Find the cellar door",
				"act": ["Something under the boards was breathing with us. Slow. Patient."]},
		],
		"end": "Marion Haskell was the last to leave Enfield town hall. She never told anyone what she heard."},
}

const ENDINGS := {
	"memory": {"title": "The City Remembers",
		"body": "In 1946 the reservoir reaches full pool and the water runs east through the aqueducts to the city. In Dorchester a man wakes humming a hymn from a meetinghouse that is now under the water. Children in the South End draw stone walls they have never seen. A woman in Back Bay sets a saucer of milk beside the kitchen tap and cannot say why."},
	"hunger": {"title": "Boston Drinks",
		"body": "In 1946 the reservoir reaches full pool and the water runs east through the aqueducts to the city. It tastes faintly of iron. Nobody in Boston dreams of the valley. For a while nobody in Boston dreams at all. There is a great deal of you now, and very little of it remembers anything."},
}
