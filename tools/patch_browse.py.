from pathlib import Path

p = Path('app/tvchannels/src/main/kotlin/dev/tvremote/channels/BrowseActivity.kt')
s = p.read_text(encoding='utf-8')

def replace_once(old, new):
    global s
    count=s.count(old)
    if count != 1:
        raise RuntimeError(f'Expected 1 occurrence, found {count}: {old[:110]!r}')
    s=s.replace(old,new,1)

def replace_block(start,end,new=''):
    global s
    if s.count(start)!=1 or s.count(end)!=1:
        raise RuntimeError(f'Block marker missing or repeated: {start[:80]!r} / {end[:80]!r}')
    a=s.index(start); b=s.index(end,a)
    s=s[:a]+new+s[b:]

# Remove imports of legacy UI/network and self-update.
for line in ['import android.app.Dialog\n','import android.widget.EditText\n','import android.widget.ScrollView\n','import androidx.recyclerview.widget.LinearLayoutManager\n','import dev.tvremote.update.Release\n','import dev.tvremote.update.SelfUpdate\n']:
    if line in s: s=s.replace(line,'',1)

replace_block('    private var others: List<List<Channel>>', '    override fun onCreate(b: Bundle?) {')
replace_once('override fun afterTextChanged(s: Editable?) { if (group == SEARCH) scheduleOthers(); filter() }','override fun afterTextChanged(s: Editable?) { filter() }')
replace_once('        state.add(TvUi.button(this, getString(R.string.country)) { countries() })\n','')
replace_once('        cc = countryOf(intent) ?: Store.country(this)','        cc = "vn"')
replace_once('        countryOf(i)?.takeIf { it != cc }?.let { cc = it; group = ALL; homeMode = true; load(false) }\n','')
replace_once('        i.getStringExtra(QUERY)?.let { group = SEARCH; homeMode = false; others = emptyList(); otherState = IDLE; find.setText(it); buildRail(); filter() }','        i.getStringExtra(QUERY)?.let { group = SEARCH; homeMode = false; find.setText(it); buildRail(); filter() }')
replace_once('        upd.check({ askUpdate(it) }, { updating(it) })\n','')
replace_block('    private fun countryOf(i: Intent?)', '    private fun columns()')
replace_block('    private fun load(fresh: Boolean) {','    /** "Downloading the channel listâ¦ 42%"', '''    private fun load(fresh: Boolean) {
        cc = "vn"
        Store.setCountry(this, cc)
        if (fresh && isList(group)) loadList(group.removePrefix(PL), true)
        all = emptyList()
        failed = false
        loading = true
        catRes = null
        countryName = "TKiPTV"
        chrome()
        io.execute {
            var previous = -2
            val channels = Catalog.iptv(this, cc, fresh) { got, total ->
                val pct = if (total > 0) (got * 100L / total).toInt().coerceIn(0, 100) else -1
                if (pct != previous) {
                    previous = pct
                    main.post {
                        if (!isDestroyed && loading) state.loading(progressWords(pct), pct)
                    }
                }
            }
            main.post {
                if (isDestroyed) return@post
                all = channels.byChannel()
                failed = channels.isEmpty()
                loading = false
                countryName = "TKiPTV"
                if (mine(group) == null && !isList(group) && group != ALL &&
                    group != SEARCH && all.none { it.first().group == group }) group = ALL
                buildRail()
                filter()
                if (!find.hasFocus()) grid.post {
                    (grid.getChildAt(0) ?: rail.getChildAt(0))?.requestFocus()
                }
            }
        }
    }

''')
replace_once('        val rem = Reminders.all(this).size\n        if (rem > 0) add(TvUi.row(this, R.drawable.ic_bell, getString(R.string.remind_list), "$rem") { remindList() }, false)   // only while there are reminders\n','')
replace_once('            GlobalIndex.release(); main.removeCallbacks(globalRun); gseq++\n','')
replace_block('            searching -> {\n','            gid != null ->', '''            searching -> {
                if (q.isEmpty()) emptyList()
                else all.mapNotNull { ch ->
                    val name = Find.fold(ch.first().name)
                    if (name.contains(q)) ch else null
                }
            }
''')
replace_once('            searching && otherState == DONE && shown.isEmpty() -> say(getString(R.string.no_match), false)\n','            searching && shown.isEmpty() -> say(getString(R.string.no_match), false)\n')
replace_once('        homeMode = false; group = SEARCH; others = emptyList(); otherState = IDLE','        homeMode = false; group = SEARCH')
replace_block('    /** The text changed: ask the global index', '    private fun say(s: String, again: Boolean)')
replace_once('        Tool(R.drawable.ic_globe, countryName.ifEmpty { getString(R.string.country) }) { countries() },\n','')
replace_once('        val rem = Reminders.all(this).size\n        if (rem > 0) item(R.drawable.ic_bell, getString(R.string.remind_list), "$rem") { remindList() }\n','')
replace_block('    private val upd by lazy { SelfUpdate', '    /** Which of the person\'s groups [ch] is in:')
replace_block('    /** The reminders set: OK on one removes it. */', '    /** One group\'s menu: pin it to the Home screen;')
replace_block('    private fun countries() {', '    override fun onKeyDown(k: Int, e: KeyEvent): Boolean {')
replace_once('    override fun onStop() { GlobalIndex.release(); super.onStop() }','    override fun onStop() { super.onStop() }')
replace_once('    override fun onDestroy() { main.removeCallbacks(globalRun); searcher.shutdownNow(); GlobalIndex.release(); watching?.let { Store.unwatch(this, it) }; io.shutdownNow(); guides.shutdownNow(); super.onDestroy() }','    override fun onDestroy() { watching?.let { Store.unwatch(this, it) }; io.shutdownNow(); guides.shutdownNow(); super.onDestroy() }')
replace_once('            val from = if (group == SEARCH && c.country.isNotEmpty() && c.country != cc) names[c.country] ?: c.group else null   // a flag and the country, for the other countries\' cards\n            h.sub.text = (on?.title ?: from ?: groupName(h.sub.context, c.group)).let { if (dead) "â $it" else it }','            h.sub.text = (on?.title ?: groupName(h.sub.context, c.group)).let { if (dead) "â $it" else it }')
replace_once('        private const val IDLE = 0; private const val LOADING = 1; private const val OFFLINE = 2; private const val DONE = 3\n','')
# Keep Categories/Shelves declarations until remaining references have been audited.
# Keep Providers.screenThread: only used for executor priority, not for fetching providers.
p.write_text(s,encoding='utf-8')
print('Patched:',p,'(',len(s.splitlines()),'lines )')
