# 🎬 استوديو الفلم السينمائي — Cinema Studio

أرضية جاهزة لصناعة أفلام وفيديوهات سينمائية **بأمر واحد**: عوالم ثلاثية الأبعاد قابلة للتحريك، كاميرا حقيقية،
أصوات سينمائية، أصوات ذكاء اصطناعي عربية، وخطوط سينمائية عربية وإنجليزية.

> كل فلم = ملف نصي واحد (`film.yaml`). تقولين لكلود: *"حرّك المشهد الثاني من اليمين لليسار وضيف رعد"*
> فيعدّل السطر ويُخرج الفيديو.

## المحتويات

| المجلد | ماذا فيه |
|---|---|
| `engine/` | المحرك: العالم ثلاثي الأبعاد، الكاميرا، الجسيمات، الألوان، النصوص، الأصوات، المخرج |
| `films/` | أفلامك — كل فلم في مجلد خاص فيه `film.yaml` وصوره |
| `sounds/` | مكتبة الأصوات السينمائية (29 صوتًا) — [استمعي](sounds/README.md) |
| `voices/` | أصوات الذكاء الاصطناعي: رجل، امرأة، طفل، راوٍ عميق، شيخ — [التفاصيل](voices/README.md) |
| `assets/fonts/` | أفضل الخطوط السينمائية العربية والإنجليزية — [التفاصيل](assets/fonts/README.md) |
| `previews/` | معاينات العوالم الجاهزة ولوحة الخطوط |
| `docs/video-instructions.md` | تعليمات كتابة الفيديو والبحث (الثابتة) |
| `CLAUDE.md` | دليل التشغيل الذي يقرؤه كلود في كل جلسة |

## التشغيل

```bash
python3 studio.py render films/demo/film.yaml            # الفلم كاملًا 1080p
python3 studio.py render films/demo/film.yaml --q 0.5    # معاينة سريعة
python3 studio.py still  films/demo/film.yaml 3.5        # لقطة ثابتة عند الثانية 3.5
python3 studio.py shot   films/demo/film.yaml 1          # مشهد واحد فقط
python3 studio.py sounds | voices | sets | fonts        # تصدير المكتبات والمعاينات
```

المتطلبات: Python 3 + numpy + scipy + opencv + Pillow (مع raqm) + PyYAML + ffmpeg.
الأصوات البشرية تُنزَّل تلقائيًا أول مرة (~350MB) إلى `~/.cache/cinema-voices`.

## العوالم الجاهزة (`set:`)

| الاسم | الوصف |
|---|---|
| `city_sunset` | مدينة بقباب ومآذن وقت الغروب |
| `desert_dusk` | صحراء وكثبان عند المغيب |
| `night_mountains` | جبال ليلية مع قمر وضباب ونجوم |
| `storm_plain` | سهل عاصف ممطر (يدعم البرق) |
| `void` | استوديو أسود لعرض العناوين والصور ثلاثية الأبعاد |

ويمكن بدل العالم الجاهز استخدام:
- `photo: صورة.jpg` — **صورتك تتحول لمشهد ثلاثي الأبعاد**: يُفصل الشخص عن الخلفية تلقائيًا
  (`subject: [x0,y0,x1,y1]` مربع تقريبي حوله) أو بصورة مقصوصة PNG منك (`subject: person.png`)،
  وتُرمَّم الخلفية خلفه، فتتحرك الكاميرا ويظهر عمق حقيقي.
- `clip: فيديو.mp4` — مقطع فيديو جاهز (مثلًا من أداة توليد فيديو) نضيف عليه الأصوات والنصوص والألوان.

## حركات الكاميرا (`camera:`)

`dolly_in` دفع للأمام · `dolly_out` رجوع · `truck_left/right` انزلاق · `crane_up/down` رافعة ·
`orbit_left/right` دوران حول الهدف · `push_tilt` · `vertigo` دوخة هيتشكوك · `roll_in` · `reveal_up` كشف من الأسفل · `drift` انجراف هادئ · `static`

مثال: `camera: {move: orbit_left, amount: 0.7, ease: smooth}` أو تحكم كامل:
`camera: {from: {x: -100, z: 0}, to: {x: 100, z: 300, roll: 3}, ease: inout}`

## المؤثرات

- جسيمات ثلاثية الأبعاد `particles:` → `dust` غبار · `embers` جمر · `snow` ثلج · `rain` مطر · `sparks` شرر · `stars` نجوم · `fireflies` يراعات
- `rays:` أشعة الضوء · `lightning: [ثوانٍ]` برق مع رعد تلقائي · `shake:` اهتزاز · `hits:` ضربة مع ارتجاج
- عمق الميدان: `aperture:` و `focus:`
- الألوان `look:` → `teal_orange` · `warm_epic` · `cold_night` · `bleach` · `noir` · `vintage`
- الانتقالات `transition:` → `cut` · `fade` · `whip` (مع صوت مرور) · `dip_black` · `flash`
- حركة الطبقات `motion:` → `breathe` · `bob` · `sway` · `float`، أو `anim: {from:{}, to:{}}` لأي خاصية (x, y, z, scale, yaw, pitch, roll, opacity)

## النصوص

`text: [{content: "...", style: epic, at: 2, pos: center, anim: zoom}]`
الأنماط: `title` · `epic` · `heritage` · `chapter` · `subtitle` · `caption` · `lower_third` · `en_title` · `en_trailer` · `en_doc`
ونص ثلاثي الأبعاد يدور في الفضاء: ضعيه في `layers:` بدل `text:` (انظري المشهد الأخير في الفلم التجريبي).

## الصوت

- `music:` موسيقى خلفية مولّدة (`pad`, `drone`, `taiko`...) وتنخفض تلقائيًا تحت صوت الراوي
- `sfx: [{name: boom, at: 3.4}]` و `{name: riser, ends_at: 3.4}` (ينتهي التصاعد لحظة الضربة)
- `ambience:` أصوات جو المشهد (يضيفها كل عالم تلقائيًا)
- `say: {text: "نص مشكول", voice: man|woman|child|deep|elder, at: 1}`

## حدود صريحة

- العوالم مرسومة رسمًا فنيًا مسطحًا متعدد الطبقات (2.5D)، وليست نماذج ثلاثية الأبعاد كاملة مثل Blender.
- **تحريك إنسان واقعي (يمشي/يأكل/يجري بحركة جسم حقيقية)** من صورة يحتاج نموذج توليد فيديو بالذكاء الاصطناعي
  (مثل Kling أو Runway أو Veo) — هذا غير متاح داخل هذا المحرك. المحرك يعطي الصورة عمقًا وحركة كاميرا وأجواء وأصواتًا،
  وإذا ولّدتِ المقطع المتحرك هناك فإن `clip:` يضيف عليه الأصوات المصاحبة لكل حركة والنصوص والألوان والراوي.

## خط الإنتاج بمستوى فيلم سليماني
النموذج: `films/soleimani_mckee/` (الفيلم `model.mp4` + الكود + الخطة). الأوامر: `new` ← `plan` ← `qa` — التفاصيل في `docs/film-pipeline.md`.
مراجع الكتابة: `docs/writing-for-animation.md` و`docs/story-mckee.md`؛ مراجع الحركة: `docs/animation-principles.md`.
