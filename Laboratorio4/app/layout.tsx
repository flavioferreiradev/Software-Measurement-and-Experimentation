import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Lab04 | Testes de hipótese por dentro",
  description: "Uma exploração visual do teste Z e do binomial exato para a taxa de falhas de CI.",
  openGraph: {
    title: "Lab04 | Testes de hipótese por dentro",
    description: "Dados reais, simulações e uma decisão estatística explicada em sete capítulos.",
    type: "website",
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="pt-BR"><body>{children}</body></html>;
}
