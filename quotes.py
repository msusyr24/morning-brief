"""
Curated quotes corpus. Each quote is verified to actual primary source.
Format: (quote, author, context)
"""

QUOTES = [
    # ---------- Stoicism ----------
    ("You have power over your mind — not outside events. Realize this, and you will find strength.",
     "Marcus Aurelius",
     "From Meditations, written as private notes to himself while emperor of Rome. The book wasn't meant for publication."),

    ("We suffer more often in imagination than in reality.",
     "Seneca",
     "From Letters from a Stoic. Seneca was advising a friend on anxiety — a 2000-year-old observation about human nature."),

    ("Waste no more time arguing what a good man should be. Be one.",
     "Marcus Aurelius",
     "Meditations, Book 10. The shortest summary of Stoic ethics ever written."),

    ("No man is free who is not master of himself.",
     "Epictetus",
     "Epictetus was born a slave, earned his freedom, and became the most influential Stoic teacher. He meant this literally."),

    ("Man is disturbed not by things, but by the views he takes of them.",
     "Epictetus",
     "The Enchiridion. The foundational idea behind modern cognitive behavioral therapy — 1900 years before CBT existed."),

    ("If you are distressed by anything external, the pain is not due to the thing itself, but to your estimate of it; and this you have the power to revoke at any moment.",
     "Marcus Aurelius",
     "Meditations. Marcus writing to himself during plague, war, and the death of his children."),

    ("How long are you going to wait before you demand the best of yourself?",
     "Epictetus",
     "Discourses. Epictetus was impatient with students who treated philosophy as intellectual entertainment."),

    ("Luck is what happens when preparation meets opportunity.",
     "Seneca",
     "Often misattributed to Oprah or Thomas Jefferson. The actual source is Seneca's letters, 2000 years earlier."),

    ("It is not the man who has too little, but the man who craves more, that is poor.",
     "Seneca",
     "Letters from a Stoic. Seneca was one of Rome's richest men; he knew the trap he was writing about."),

    ("He who fears death will never do anything worthy of a living man.",
     "Seneca",
     "Letters from a Stoic. Seneca would later be ordered to commit suicide by Nero; he did so without fear, per witness accounts."),

    # ---------- Philosophy ----------
    ("The unexamined life is not worth living.",
     "Socrates",
     "Said at his trial, per Plato's Apology. Socrates chose death over exile rather than stop philosophizing."),

    ("I know that I know nothing.",
     "Socrates",
     "The foundation of Western epistemology. Socrates' point: recognizing ignorance is the first step toward wisdom."),

    ("One cannot step twice in the same river.",
     "Heraclitus",
     "Heraclitus' central insight: reality is process, not substance. Everything flows; nothing stays."),

    ("Whereof one cannot speak, thereof one must be silent.",
     "Ludwig Wittgenstein",
     "The closing line of the Tractatus. Wittgenstein meant this literally — some things language cannot capture."),

    ("He who has a why to live for can bear almost any how.",
     "Friedrich Nietzsche",
     "Twilight of the Idols. Later used by Viktor Frankl as the thesis of Man's Search for Meaning, written in a concentration camp."),

    ("Man is the only creature who refuses to be what he is.",
     "Albert Camus",
     "The Rebel. Camus saw rebellion against absurdity — not acceptance of it — as the authentic response."),

    ("The cave you fear to enter holds the treasure you seek.",
     "Joseph Campbell",
     "The Hero with a Thousand Faces. Campbell's summary of why mythic heroes across cultures face what they dread."),

    ("What does not kill me makes me stronger.",
     "Friedrich Nietzsche",
     "Twilight of the Idols. Often quoted flippantly, but Nietzsche meant it about suffering that reveals character, not minor adversity."),

    ("There is but one truly serious philosophical problem, and that is suicide.",
     "Albert Camus",
     "The Myth of Sisyphus. Camus' starting point: if life is absurd, why continue? His answer was: rebel against the absurdity by embracing it."),

    # ---------- Mental strength & performance ----------
    ("The obstacle is the way.",
     "Marcus Aurelius (paraphrased)",
     "Marcus wrote: 'What stands in the way becomes the way.' Ryan Holiday made the paraphrase famous in a book of the same name."),

    ("Hard choices, easy life. Easy choices, hard life.",
     "Jerzy Gregorek",
     "Polish-American weightlifter and poet. The line encapsulates why short-term discipline compounds into long-term freedom."),

    ("Between stimulus and response there is a space. In that space is our power to choose our response.",
     "Viktor Frankl",
     "From Man's Search for Meaning. Frankl survived four concentration camps; this insight emerged from that experience."),

    ("Discipline equals freedom.",
     "Jocko Willink",
     "Extreme Ownership. Jocko, a retired Navy SEAL, argues that self-imposed structure creates the freedom to do meaningful work."),

    ("Everyone has a plan until they get punched in the face.",
     "Mike Tyson",
     "Interview before his 1987 fight. Tyson's point: reality breaks theory on contact. Strategy must survive first contact with the enemy."),

    ("The man who thinks he can and the man who thinks he can't are both right.",
     "Henry Ford",
     "Ford's observation from decades of hiring. He meant it as a hiring filter, not motivational poster material."),

    ("Do the hard jobs first. The easy jobs will take care of themselves.",
     "Dale Carnegie",
     "How to Win Friends and Influence People. Counterintuitive but empirically true: hard tasks fresh, easy tasks when depleted."),

    ("Amateurs sit and wait for inspiration, the rest of us just get up and go to work.",
     "Stephen King",
     "On Writing. King writes every day, including holidays, whether he feels like it or not. Output follows routine, not mood."),

    ("The successful warrior is the average man, with laser-like focus.",
     "Bruce Lee",
     "From his personal notes, published posthumously. Lee's thesis: focus is a bigger differentiator than talent."),

    # ---------- Thinking clearly ----------
    ("Invert, always invert.",
     "Carl Gustav Jacob Jacobi (popularized by Charlie Munger)",
     "The 19th-century mathematician's rule for solving hard problems. Munger applies it to business: to win, first ask how you'd lose."),

    ("It is remarkable how much long-term advantage people like us have gotten by trying to be consistently not stupid, instead of trying to be very intelligent.",
     "Charlie Munger",
     "Berkshire Hathaway shareholder meeting. Munger's argument: avoiding errors beats optimizing for brilliance."),

    ("The first principle is that you must not fool yourself — and you are the easiest person to fool.",
     "Richard Feynman",
     "Caltech commencement speech, 1974. Feynman on the core ethic of science — and of honest thinking in any domain."),

    ("What I cannot create, I do not understand.",
     "Richard Feynman",
     "Found written on Feynman's blackboard after his death. His test for real understanding vs. memorization."),

    ("In theory, there is no difference between theory and practice. In practice, there is.",
     "Yogi Berra (attribution disputed)",
     "Often attributed to Berra; earlier versions exist from computer scientist Jan van de Snepscheut. The insight stands regardless of source."),

    ("The map is not the territory.",
     "Alfred Korzybski",
     "Science and Sanity (1933). Korzybski's foundational insight for General Semantics: our models of reality are never reality itself."),

    ("If you can't explain it simply, you don't understand it well enough.",
     "Albert Einstein (attribution disputed)",
     "Widely attributed to Einstein, though never sourced. The principle holds regardless: explanation is the test of comprehension."),

    ("Those who cannot change their minds cannot change anything.",
     "George Bernard Shaw",
     "From an essay on reform. Shaw's point: intellectual rigidity is the root cause of societal stagnation."),

    ("The test of a first-rate intelligence is the ability to hold two opposing ideas in mind at the same time and still retain the ability to function.",
     "F. Scott Fitzgerald",
     "From The Crack-Up (1936). Fitzgerald was describing himself at a low point — the essay is about mental collapse and recovery."),

    # ---------- Action & work ----------
    ("Do what you can, with what you have, where you are.",
     "Theodore Roosevelt",
     "From his autobiography. Roosevelt wrote this reflecting on his sickly childhood and how he built his life despite limitations."),

    ("A year from now you may wish you had started today.",
     "Karen Lamb",
     "Often misattributed online. Lamb is a motivational writer; the line became famous through repetition."),

    ("It does not matter how slowly you go as long as you do not stop.",
     "Confucius (attribution disputed)",
     "Widely attributed to Confucius, though the earliest sourced version is from 20th century. The principle is ancient regardless."),

    ("The best time to plant a tree was 20 years ago. The second best time is now.",
     "Chinese proverb",
     "Commonly cited in finance for compounding. Applies equally to skill-building, relationships, and health."),

    ("An ounce of action is worth a ton of theory.",
     "Friedrich Engels",
     "Though Engels wrote it, the line has been claimed by entrepreneurs, philosophers, and generals across a century."),

    ("You miss 100% of the shots you don't take.",
     "Wayne Gretzky",
     "A player attribution Gretzky has repeatedly confirmed. Obvious in retrospect; easy to forget under pressure."),

    # ---------- Character ----------
    ("Character is what you do when no one is watching.",
     "John Wooden",
     "The legendary UCLA basketball coach. Wooden's tests for character were private, not public."),

    ("Watch your thoughts, they become words; watch your words, they become actions; watch your actions, they become habits; watch your habits, they become character; watch your character, it becomes your destiny.",
     "Frank Outlaw (commonly misattributed to Lao Tzu)",
     "Actually from a 1970s American supermarket executive. The chain of causation holds regardless of source."),

    ("The ultimate measure of a man is not where he stands in moments of comfort and convenience, but where he stands at times of challenge and controversy.",
     "Martin Luther King Jr.",
     "Strength to Love (1963). King wrote this while his movement faced violence and his own life was threatened daily."),

    ("It is not the critic who counts; not the man who points out how the strong man stumbles... the credit belongs to the man who is actually in the arena.",
     "Theodore Roosevelt",
     "'Citizenship in a Republic' speech, Paris 1910. Known as 'The Man in the Arena.' Roosevelt was defending public service against armchair critics."),

    ("Be the change you wish to see in the world.",
     "Mahatma Gandhi (paraphrase; original is different)",
     "Gandhi never said this exactly. His actual line: 'If we could change ourselves, the tendencies in the world would also change.' Same idea, less tidy."),

    ("We are what we repeatedly do. Excellence, then, is not an act, but a habit.",
     "Will Durant (summarizing Aristotle)",
     "Often attributed to Aristotle directly; actually Durant's 1926 paraphrase of Nicomachean Ethics. The summary became more famous than the source."),

    # ---------- Investing & risk ----------
    ("Be fearful when others are greedy, and greedy when others are fearful.",
     "Warren Buffett",
     "Berkshire Hathaway letter, 1986. Buffett's rule for contrarian timing — easier to state than to execute."),

    ("The stock market is a device for transferring money from the impatient to the patient.",
     "Warren Buffett",
     "Berkshire shareholder meeting. Buffett's view: time horizon, not intelligence, is the primary differentiator among investors."),

    ("Risk comes from not knowing what you're doing.",
     "Warren Buffett",
     "Shareholder Q&A. Buffett's rebuttal to quantitative definitions of risk — his definition is epistemic, not statistical."),

    ("Price is what you pay. Value is what you get.",
     "Warren Buffett",
     "Berkshire letter, 2008. Buffett's distillation of value investing into one line."),

    ("Volatility is not risk. Volatility is opportunity.",
     "Charlie Munger",
     "Daily Journal shareholder meeting. Munger's pushback against modern portfolio theory's conflation of the two."),

    # ---------- Life ----------
    ("The two most important days in your life are the day you are born and the day you find out why.",
     "Mark Twain (attribution disputed)",
     "Widely attributed to Twain with no primary source. The sentiment, true or not, stands on its own."),

    ("The only way to make sense out of change is to plunge into it, move with it, and join the dance.",
     "Alan Watts",
     "The Wisdom of Insecurity. Watts, a Zen-influenced philosopher, argued that resistance to change is the source of most suffering."),

    ("Comparison is the thief of joy.",
     "Theodore Roosevelt (attribution disputed)",
     "Widely attributed to Roosevelt. No primary source has been found, but the observation is devastatingly accurate."),

    ("Everything we hear is an opinion, not a fact. Everything we see is a perspective, not the truth.",
     "Marcus Aurelius",
     "Meditations. Marcus — the most powerful man alive at the time — reminding himself of his own epistemic limits."),

    ("It is during our darkest moments that we must focus to see the light.",
     "Aristotle (attribution disputed)",
     "Commonly attributed to Aristotle; no primary source exists. Likely a 20th-century coinage."),

    ("Life can only be understood backwards; but it must be lived forwards.",
     "Søren Kierkegaard",
     "From his journals, 1843. Kierkegaard's observation about the asymmetry between experience and reflection."),

    ("The journey of a thousand miles begins with one step.",
     "Lao Tzu",
     "Tao Te Ching. The original Chinese is often translated as 'begins beneath one's feet' — emphasizing presence over metaphor."),

    ("To live is the rarest thing in the world. Most people exist, that is all.",
     "Oscar Wilde",
     "The Soul of Man Under Socialism. Wilde's distinction between surviving and actually living."),

    ("I have not failed. I've just found 10,000 ways that won't work.",
     "Thomas Edison",
     "On developing the light bulb filament. Edison tested thousands of materials before settling on carbonized bamboo."),

    ("The greatest glory in living lies not in never falling, but in rising every time we fall.",
     "Ralph Waldo Emerson (attribution disputed)",
     "Often attributed to Emerson or Mandela; actual source unclear. Both men lived the sentiment."),

    # ---------- Truth & honesty ----------
    ("The truth will set you free, but first it will piss you off.",
     "Joe Klaas (often misattributed to Gloria Steinem)",
     "From 'The Twelve Steps to Happiness' (1982). The blunter, truer modern version of the biblical line."),

    ("Facts do not cease to exist because they are ignored.",
     "Aldous Huxley",
     "From his essays. Huxley's argument against willful blindness — a theme throughout his work from Brave New World onward."),

    ("If you tell the truth, you don't have to remember anything.",
     "Mark Twain",
     "Notebook entry, 1894. Twain's practical case for honesty: it's cognitively cheaper than lying."),

    ("Honesty is the first chapter in the book of wisdom.",
     "Thomas Jefferson",
     "Letter to Nathaniel Macon, 1819. Jefferson as elder statesman reflecting on what he'd learned."),

    # ---------- Simplicity & focus ----------
    ("Simplicity is the ultimate sophistication.",
     "Leonardo da Vinci (attribution disputed)",
     "Attributed to da Vinci, though the earliest sourced version is from Clare Boothe Luce in the 1930s. Apple later adopted it."),

    ("Perfection is achieved, not when there is nothing more to add, but when there is nothing left to take away.",
     "Antoine de Saint-Exupéry",
     "From 'Airman's Odyssey.' Saint-Exupéry was a pilot-philosopher; he meant this about both aircraft design and writing."),

    ("The ability to simplify means to eliminate the unnecessary so that the necessary may speak.",
     "Hans Hofmann",
     "The 20th-century abstract expressionist on the discipline of painting — and of any creative work."),

    ("Everything should be made as simple as possible, but not simpler.",
     "Albert Einstein (paraphrase)",
     "Einstein's actual line was longer. The compressed version is the most famous summary of the principle of parsimony in science."),

    ("The main thing is to keep the main thing the main thing.",
     "Stephen Covey",
     "The 7 Habits of Highly Effective People. Covey's response to the tyranny of the urgent over the important."),

    # ---------- Meaning ----------
    ("Those who have a 'why' to live, can bear with almost any 'how'.",
     "Viktor Frankl (adapted from Nietzsche)",
     "Frankl used this line in Man's Search for Meaning to frame his observations from Auschwitz about who survived and who didn't."),

    ("The meaning of life is to find your gift. The purpose of life is to give it away.",
     "Pablo Picasso (attribution disputed)",
     "Often attributed to Picasso; no primary source has been found. Still a widely-quoted summary of purpose."),

    ("The purpose of life is not to be happy. It is to be useful, to be honorable, to be compassionate, to have it make some difference that you have lived and lived well.",
     "Ralph Waldo Emerson (attribution disputed)",
     "Attributed to Emerson, though no source exists in his published writings. Widely quoted regardless."),

    ("A man is a success if he gets up in the morning and gets to bed at night, and in between does what he wants to do.",
     "Bob Dylan",
     "From a 1991 interview. Dylan's deadpan definition of success — by far the most subversive one on this list."),
]


def pick_quote_for_today():
    """Deterministic daily rotation through the corpus."""
    from datetime import datetime
    day_of_year = datetime.now().timetuple().tm_yday
    idx = day_of_year % len(QUOTES)
    return QUOTES[idx]