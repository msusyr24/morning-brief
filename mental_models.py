"""
Munger's mental models, with teaching stories and famous applications.
Based on the canonical list from Poor Charlie's Almanack and Munger's speeches.
Format: (name, domain, teaching_story)
"""

MODELS = [
    # ---------- Psychology (Munger's "Psychology of Human Misjudgment") ----------
    ("Incentive-Caused Bias", "Psychology",
     "Munger on FedEx: the company couldn't get packages sorted on time until they stopped paying workers by the hour and started paying by the shift. Workers had been incentivized to drag out the job. Once the incentive flipped, the bottleneck vanished overnight. Whenever a system produces strange behavior, ask: what is it paying for?"),

    ("Reciprocity Tendency", "Psychology",
     "When someone does you a small favor, you feel pressure to return it — often with interest. Hare Krishnas used this by giving flowers at airports before asking for donations. The cost of a flower vs. the guilt of not reciprocating was wildly asymmetric. Aware of this tendency, you can watch for it in negotiations, sales pitches, and favors-exchanged-for-favors politics."),

    ("Social Proof", "Psychology",
     "When uncertain, humans copy others. Munger cites the Jonestown massacre: once a few people drank the poison, social proof cascaded through 900. Less horrifically: laugh tracks work because we're wired to follow the crowd. The implication: in ambiguous situations, don't check what others are doing — check the underlying reality."),

    ("Contrast Misreaction", "Psychology",
     "We judge things relative to recent comparisons, not absolute values. A $2,000 suit feels cheap after you've committed to a $30,000 car. Real estate agents show you a worse house first. Munger: 'If you're selling something, show the dud first.' If you're buying, beware of contrast-engineered comparisons."),

    ("Availability Bias", "Psychology",
     "What's easily recalled feels more common. Plane crashes dominate the news, so flying feels more dangerous than driving — despite driving being ~100x deadlier per mile. Munger's defense: when estimating frequency, write down actual numbers, don't trust your gut's sense of 'how often this happens.'"),

    ("Commitment and Consistency", "Psychology",
     "Once we commit publicly, we distort reality to stay consistent. Cults exploit this with small initial commitments (a meeting, a donation) that escalate. Munger's rule: be very careful what you commit to publicly. Once you've said it, your brain will defend it against evidence."),

    ("Envy / Jealousy Tendency", "Psychology",
     "Munger: 'It's not greed that drives the world, but envy.' Warren Buffett has said the same. People tolerate being poor; they don't tolerate their neighbor being richer. Whole industries (luxury goods, social media) monetize this tendency. Personal application: track your mental state when you encounter peers' successes."),

    ("Deprival Super-Reaction", "Psychology",
     "Losing $100 feels worse than finding $100 feels good — by about 2x, per Kahneman's research. Munger calls this 'deprival super-reaction.' It explains stock-market panics, breakup grief, and why people fight harder to keep what they have than to acquire what they don't. Knowing this, you can price losses more rationally."),

    ("Authority-Misinfluence Tendency", "Psychology",
     "We defer to perceived authority, often past the point of sense. Milgram's experiments: subjects delivered 'lethal' shocks because a lab coat said to. Real-world: pilots crashing planes because captains made errors first-officers wouldn't challenge. Defense: evaluate the claim, not the credential."),

    ("Lollapalooza Effect", "Psychology",
     "Munger's own coinage for when multiple biases converge on the same outcome. Example: auction fever combines commitment bias, social proof, contrast bias, and deprival super-reaction — all pushing the bidder the same way. When you're making a decision and several biases happen to agree, be most suspicious, not least."),

    # ---------- Math & statistics ----------
    ("Inversion", "Math/Logic",
     "Munger: 'Invert, always invert.' Jacobi's rule for hard problems. Instead of 'how do I succeed?' ask 'how do I fail?' — then systematically avoid those paths. Charlie on investing: 'We spend more time thinking about how to avoid stupidity than how to be brilliant, because stupidity is easier to recognize and the payoff is bigger.'"),

    ("Base Rates", "Math/Statistics",
     "When evaluating any individual case, start with the frequency across the population. Restaurants fail ~60% in year one — no matter how passionate your friend's pitch is, that's your prior. Doctors miss this constantly: a positive test for a rare disease is usually a false positive, even if the test is 95% accurate. Anchor on the base rate before adjusting for specifics."),

    ("Bayesian Updating", "Math/Statistics",
     "New evidence should shift your beliefs proportional to how surprising it is. Most people either anchor too hard on priors or overreact to recent news. The discipline: state your prior, see the evidence, update — but by how much the evidence would change things, not how much it feels like it should."),

    ("Compound Interest", "Math",
     "Einstein allegedly called it the eighth wonder of the world. More important: the same math governs skills, relationships, reputation, and physical decline. Small daily inputs compound into massive differences over decades. Munger: 'The first rule of compounding: never interrupt it unnecessarily.'"),

    ("Permutations and Combinations", "Math",
     "The number of possible arrangements grows explosively. In business: small product differences create exponentially different customer experiences. In investing: portfolios of uncorrelated bets dominate concentrated ones over time, mathematically. Munger uses this to argue for breadth of mental models."),

    ("Law of Large Numbers", "Math/Statistics",
     "Over many trials, averages converge to expected values — but in the short run, anything can happen. Casinos know this; gamblers forget it. Applied to life: don't judge strategies by single outcomes. A good decision can have a bad result, and vice versa."),

    # ---------- Physics & engineering ----------
    ("Critical Mass", "Physics",
     "Below a threshold, a reaction dies. Above it, it runs away. Munger applies this to businesses: Costco reached a member density where its cost structure became impossible to replicate. Below critical mass, companies starve. The question for any venture: what's the minimum scale needed to self-sustain?"),

    ("Feedback Loops", "Engineering/Systems",
     "Every system has loops — reinforcing (compounding) or balancing (self-correcting). Social media engagement: reinforcing. Thermostat: balancing. Identifying which type of loop you're in tells you what to expect. Reinforcing loops go to extremes without external intervention."),

    ("Breakpoints", "Physics/Systems",
     "Systems often behave smoothly until a threshold, then change discontinuously. Water at 99°C looks like water at 99°C looks like water at 99°C. Then at 100°C, it's steam. Business analogue: a company can look fine until a cash flow breakpoint is crossed, then collapse in weeks. Watch for thresholds, not trends."),

    ("Entropy / Second Law of Thermodynamics", "Physics",
     "Systems tend toward disorder without energy input. Gardens return to weeds, teams drift toward dysfunction, code rots. Munger: 'Reality has a relentless downhill slope; you have to pedal constantly just to stay in place.' Applied to any endeavor: what's eroding, and what energy am I spending to hold it together?"),

    ("Equilibrium", "Physics/Economics",
     "Systems settle into balances where forces cancel. Markets find price equilibrium; ecosystems find predator-prey balance; workplaces find culture equilibrium. Shifting equilibrium requires changing underlying forces, not fighting symptoms. Munger applies this to regulation: treat symptoms and you'll return to equilibrium; change incentives and the new equilibrium shifts."),

    # ---------- Biology ----------
    ("Evolution by Natural Selection", "Biology",
     "Variation + selection + inheritance produces adaptation over time, with no designer. Applies beyond biology: successful companies aren't designed — they're selected from thousands of variations that failed. Industries evolve. Ideas evolve. Your own career evolves the same way, whether you acknowledge it or not."),

    ("Niches / Ecosystems", "Biology",
     "Organisms specialize to exploit specific conditions. Same in business: dominant companies usually own a niche, not a 'market.' Munger on See's Candies: it didn't try to beat Hershey's; it owned the boxed-chocolate-as-gift niche. Ask: what's my niche, and what erodes it?"),

    ("Symbiosis / Mutualism", "Biology",
     "Some species co-evolve to benefit each other. Businesses too: Microsoft + Intel, Visa + banks, YouTube + creators. The strongest business relationships aren't zero-sum — they're symbiotic. When evaluating partnerships, ask: does this create a new value pool, or just split an existing one?"),

    # ---------- Economics ----------
    ("Supply and Demand", "Economics",
     "Prices are signals, not values. When something is scarce relative to demand, its price rises until demand drops or supply increases. Most people ignore this when buying bubbles (tulips, crypto) or selling panics (2008 real estate). Munger's defense: always ask, 'relative to what supply, and what demand level?'"),

    ("Opportunity Cost", "Economics",
     "The true cost of any choice is the best alternative you gave up. Munger: 'Intelligent people make decisions based on opportunity costs.' If your money earns 8% elsewhere, a 6% opportunity is actually a loss of 2%. Applied broadly: every yes to one thing is a no to others."),

    ("Comparative Advantage", "Economics",
     "Each party should focus on what they're relatively best at, and trade. Ricardo's 1817 insight that still governs global trade. Personal application: don't do what you're merely good at — do what you're best at relative to others, and delegate the rest."),

    ("Economies of Scale", "Economics",
     "Costs per unit often drop as volume grows. This is why Walmart crushes small competitors and why networks (like social media) concentrate to winners. Munger's warning: some businesses have dis-economies of scale (bureaucracy, coordination costs). Distinguish which you're in."),

    ("Network Effects", "Economics",
     "The value of a product grows with the number of users. Telephones, Facebook, credit cards. Once critical mass is reached, displacement becomes nearly impossible. The moat isn't the product — it's the user base. Munger invested in See's, American Express, and Coca-Cola partly on this basis."),

    ("Moats / Competitive Advantage", "Economics/Business",
     "Buffett's word for what prevents competitors from stealing profits. Brand (Coca-Cola), switching costs (SAP), network effects (Visa), scale (Walmart), regulation (utilities). Without a moat, profits get competed to zero. Munger's question on any business: what's the moat, and is it widening or narrowing?"),

    ("Marginal Utility", "Economics",
     "Each additional unit of something is usually worth less than the previous. The first slice of pizza beats the tenth. Applied: diminishing returns govern almost every effort — study, exercise, relationships. At some point, more input produces less output. Know where that point is for your main endeavors."),

    # ---------- Business & strategy ----------
    ("Circle of Competence", "Business/Epistemics",
     "Buffett: 'Know the edge of your competence, and stay within it.' The edge matters more than the size. A small, well-understood circle beats a large, fuzzy one. Munger's addition: most investment disasters come from people who didn't know where their circle ended."),

    ("Margin of Safety", "Business/Risk",
     "Ben Graham's principle: buy with enough buffer that you're right even if you're somewhat wrong. Applied to bridge engineering: engineers specify 4x the load the bridge will ever see. Applied to life: leave room for error — in financial reserves, in timing, in relationships. The world is less predictable than we think."),

    ("Punch-Card Investing", "Business/Decision-making",
     "Buffett's thought experiment: imagine you had a punch card with only 20 slots for investment decisions in your lifetime. You'd be far more careful. Apply this discipline to career moves, major purchases, commitments. Scarcity forces quality."),

    ("Cost-Benefit Analysis", "Business",
     "Sum expected benefits, subtract expected costs (including opportunity cost), proceed if positive. Obvious in principle, rarely done in practice — we substitute emotion, anchoring, or social proof. The discipline: actually write it down. Numbers on paper expose magical thinking."),

    # ---------- Epistemics ----------
    ("Falsifiability", "Philosophy of Science",
     "Karl Popper: a claim is scientific only if it could, in principle, be proven false. 'My theory explains everything' is a warning sign, not a strength. Munger uses this to evaluate business claims: if a strategy works in every conceivable market, it probably has no real mechanism."),

    ("Second-Order Thinking", "Thinking",
     "First-order: 'If I do X, what happens?' Second-order: 'Then what? And then what?' Howard Marks's favorite tool. Most people stop at first-order and miss consequences. Munger on Coca-Cola: first-order says 'sell sugar water.' Second-order says 'build a distribution and brand system that generates returns for a century.'"),

    ("Occam's Razor", "Logic",
     "When multiple explanations fit the evidence, prefer the simplest one. Not because simple is always right — because simple is easier to test and refute. Overcomplicated theories usually survive only because they're hard to disprove, not because they're true."),

    ("Hanlon's Razor", "Epistemics",
     "Never attribute to malice what can be adequately explained by incompetence or inattention. The world has vastly more incompetent people than evil ones. Most perceived slights are accidents. Before assuming conspiracy, assume bandwidth limits."),

    ("Chesterton's Fence", "Epistemics",
     "Before removing a rule or system you don't understand, figure out why it was put there. Every rule was someone's solution to a problem. If you can't articulate the problem, you might be about to recreate it. Munger applies this to business reorganizations: understand the old structure first."),

    ("Confirmation Bias", "Epistemics",
     "We seek evidence that confirms what we already believe, and dismiss what doesn't. Charles Darwin's rule: when he encountered evidence against his pet theories, he'd immediately write it down, because he knew he'd forget it otherwise. Deliberate contrarian reading is the only known antidote."),

    ("Survivorship Bias", "Epistemics",
     "We see the winners and forget the losers who didn't make it. Successful entrepreneurs' advice is biased toward the strategies of survivors, ignoring the identical strategies of people who failed. WWII example: engineers wanted to armor the parts of returning planes with bullet holes — until Abraham Wald pointed out the planes that didn't return were hit elsewhere."),

    # ---------- Decision-making ----------
    ("Expected Value", "Decision-making",
     "Probability-weighted outcomes. A 10% chance at $1M is worth more than a 90% chance at $100K — but most people grab the latter, fearing the 90% loss. Munger: 'If you can get comfortable with expected value, you'll make decisions 99% of people can't.'"),

    ("Asymmetric Bets", "Decision-making",
     "Seek situations where downside is limited but upside is unbounded. Options trading, venture capital, writing a book. Conversely, avoid inverses: picking up pennies in front of a steamroller. Nassim Taleb's full framework, but Munger lived it before Taleb wrote about it."),

    ("Convexity vs. Concavity", "Risk/Mathematics",
     "Convex payoffs benefit from volatility (options, bets with capped losses). Concave payoffs are hurt by volatility (leverage, short-term trading). Life structures that are convex compound in your favor; concave structures blow up eventually. Structure your life to be convex where possible."),

    ("Two-Track Analysis", "Decision-making",
     "Munger's discipline for every decision: Track 1 — what do the rational factors say? Track 2 — what subconscious factors (fear, ego, envy) might be pushing me? Making the second track explicit is the only way to neutralize it."),

    # ---------- Communication & persuasion ----------
    ("Scarcity", "Psychology/Persuasion",
     "Rare things seem more valuable. Advertisers manufacture scarcity ('limited time offer'). Cialdini's research: made-up scarcity works nearly as well as real scarcity. Defense: before valuing something for its scarcity, ask whether it's genuinely scarce or artificially gated."),

    ("Framing", "Communication",
     "How something is presented changes how it's received, even when content is identical. '10% fat' sells worse than '90% lean.' Surgery 'with a 90% survival rate' sells better than one 'with a 10% death rate.' Know this both to resist manipulation and to communicate more clearly."),

    ("Principle-Agent Problem", "Economics/Business",
     "When one party (agent) acts on behalf of another (principal), their incentives rarely perfectly align. Lawyers bill by the hour, not by outcome. CEOs optimize for short-term stock price, not long-term company health. The discipline: in any relationship, ask whose incentives actually match yours."),

    # ---------- Focus ----------
    ("Pareto Principle (80/20)", "Economics/Productivity",
     "Roughly 80% of effects come from 20% of causes, across almost every domain. 80% of sales from 20% of customers, 80% of crime from 20% of criminals, 80% of your happiness from 20% of your activities. The skill: identifying the 20% before wasting effort on the 80%."),

    ("Five Whys", "Problem-solving",
     "Toyota's technique: when a problem surfaces, ask 'why?' five times. Each answer gets you closer to root cause. The first answer is always a symptom, not a cause. Munger uses this in business analysis: 'Why is this company losing money?' → five layers deep, you usually find a cultural or strategic issue, not an operational one."),

    ("Ockham's Broom", "Epistemics",
     "Biologist Sydney Brenner's coinage: theorists use it to 'sweep under the rug' inconvenient facts that don't fit their model. Watch for it in any big theory — yours included. The facts being ignored are usually the most important ones."),

    # ---------- Time & change ----------
    ("Regression to the Mean", "Statistics",
     "Extreme outcomes tend to be followed by more average ones. The best quarter is usually followed by a worse one. The worst employee review is usually followed by improvement. Don't mistake regression to the mean for real change — or for the failure of it."),

    ("Path Dependence", "Systems/History",
     "Where you are now depends on the path you took to get here, not just your endpoint. QWERTY keyboards, VHS vs. Betamax, English as lingua franca. Once a path is established, switching costs often preserve it against better alternatives. Look for what's locked in by history, not optimality."),

    ("Phase Transitions", "Physics/Systems",
     "Gradual change often produces sudden transformation — ice to water, liquid to gas, dissatisfaction to revolution. Munger on markets: they look stable until they don't, because the underlying conditions were changing gradually all along. Don't be fooled by apparent stability."),

    # ---------- Human nature ----------
    ("Hedonic Adaptation", "Psychology",
     "We return to a baseline happiness level after most positive or negative events. Lottery winners are no happier a year later; paraplegics are not as unhappy as you'd predict. Implication: structural changes to daily life matter more than peak events. Optimize for the day-to-day, not the milestones."),

    ("Loss Aversion", "Psychology/Economics",
     "People feel losses about 2x as strongly as equivalent gains. Explains why sellers demand higher prices than buyers will pay for identical items, why stock-market crashes create panic but booms don't create equivalent euphoria. Knowing this, price your decisions by the rational metric, not the emotional one."),

    ("Halo Effect", "Psychology",
     "A positive impression in one area leaks into unrelated judgments. Attractive people are assumed to be smarter. Successful CEOs are assumed to be wise about unrelated topics. Strip the halo before trusting any judgment."),

    # ---------- Strategy ----------
    ("OODA Loop", "Strategy/Military",
     "Colonel John Boyd's framework: Observe, Orient, Decide, Act — then repeat, faster than your opponent. The faster your loop, the more control you have. Applies to fighter pilots, startups, and personal decisions. Most people are stuck in 'Orient' — paralyzed by analysis — while faster actors run circles around them."),

    ("Maginot Line Thinking", "Strategy",
     "France's WWI-era defense, designed against the last war, was simply bypassed in WWII. Generals always fight the last war. Companies always defend the last market. Individuals always prepare for the last threat. Ask: what if the threat doesn't come from where I'm defending?"),

    ("Hedgehog vs. Fox", "Strategy/Thinking",
     "Isaiah Berlin's distinction: the fox knows many things; the hedgehog knows one big thing. Philip Tetlock's research: on forecasting, foxes beat hedgehogs decisively. Hedgehogs commit to grand narratives and defend them past the evidence. Foxes stay flexible. For understanding the world, be a fox."),

    # ---------- Self-knowledge ----------
    ("Dunning-Kruger Effect", "Psychology",
     "Incompetent people overestimate their competence; experts underestimate theirs. The bottom 10% of performers often rate themselves above average. The top 10% doubt themselves. Defense: always seek external calibration. Your own assessment is least reliable where it matters most."),

    ("Feynman Technique", "Learning",
     "Richard Feynman's test for understanding: explain the concept in simple language, as if to a child. Gaps in your explanation reveal gaps in your understanding. If you can't do it simply, you don't know it. Apply to anything you claim to understand — and watch your knowledge recalibrate."),

    ("Beginner's Mind (Shoshin)", "Philosophy/Learning",
     "Zen concept: approach familiar things as if seeing them for the first time. Experts often see less than novices because their assumptions filter reality. Munger: 'The single most important habit is learning to be a learning machine — which requires staying ignorant on purpose, over and over.'"),
]


def pick_model_for_today():
    """Deterministic daily rotation."""
    from datetime import datetime
    day_of_year = datetime.now().timetuple().tm_yday
    idx = day_of_year % len(MODELS)
    return MODELS[idx]