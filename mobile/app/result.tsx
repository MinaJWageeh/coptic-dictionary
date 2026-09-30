import { useFocusEffect } from "expo-router";
import { useCallback, useState } from "react";
import { Text, View } from "react-native";
import { ResultCard } from "../src/components/ResultCard";
import { PrimaryButton, Screen } from "../src/components/Screen";
import { getLastTranslation, saveFavorite, type SavedTranslation } from "../src/storage";
import { sharedStyles } from "../src/theme";

export default function ResultScreen() {
  const [item, setItem] = useState<SavedTranslation | null>(null);
  const [saved, setSaved] = useState(false);

  useFocusEffect(
    useCallback(() => {
      getLastTranslation().then((value) => {
        setItem(value);
        setSaved(false);
      });
    }, [])
  );

  return (
    <Screen>
      <View>
        <Text style={sharedStyles.eyebrow}>النتيجة</Text>
        <Text style={sharedStyles.title}>تفاصيل الترجمة والثقة.</Text>
        <Text style={sharedStyles.subtitle}>هنا تظهر نتيجة الكلمة أو الجملة بشكل مختلف مع المصادر والأمثلة.</Text>
      </View>

      {item ? (
        <>
          <PrimaryButton
            label={saved ? "تم الحفظ في المفضلة" : "احفظ في المفضلة"}
            onPress={async () => {
              await saveFavorite(item);
              setSaved(true);
            }}
          />
          <ResultCard inputText={item.inputText} result={item.result} />
        </>
      ) : (
        <View style={sharedStyles.panel}>
          <Text style={sharedStyles.muted}>لا توجد نتيجة بعد. ابدأ من شاشة الترجمة.</Text>
        </View>
      )}
    </Screen>
  );
}
