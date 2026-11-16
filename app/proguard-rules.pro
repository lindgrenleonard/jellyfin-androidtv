# Custom build R8 rules.
# Shrink and optimize, but keep class/member names. This avoids breaking any
# name-based reflection and keeps crash stack traces readable.
-dontobfuscate
-keepattributes SourceFile,LineNumberTable,*Annotation*,Signature,InnerClasses,EnclosingMethod

# Markwon checks for the optional strikethrough extension at runtime
-dontwarn org.commonmark.ext.gfm.strikethrough.Strikethrough
