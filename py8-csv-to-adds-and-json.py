#!/usr/bin/env python3
import csv, json, re

fullCSV = 'out/from-repo.csv' # 'out/errors-marked.csv'
targetJSON = 'out/sheet-music-lib-data-search.js'
targetHTML = 'out/html-checkboxes.html'


composerList = [['AbtF', 'Abt', 'F.', '(1819–1885)'],
                ['AdamA', 'Adam', 'A.', '(1803–1856)'],
                ['AdamsS', 'Adams', 'S.', '(1844–1913)'],
                ['AguadoD', 'Aguado', 'D.', '(1784–1849)'],
                ['AlbenizIMF', 'Albéniz', 'I. M. F.', '(1860–1909)'],
                ['AlkanCV', 'Alkan', 'C.-V.', '(1813–1888)'],
                ['AllegriG', 'Allegri', 'G.', '(c.1582–1652)'],
                ['AlyabyevA', 'Alyabyev', 'A.', '(1787–1851)'],
                ['AmendolaA', 'Amendola', 'A.', '(?–?)'],
                ['AndreJ', 'André', 'J.', '(1741–1799)'],
                ['Anonymous', 'Anonymous', '', ''],
                ['ArbanJB', 'Arban', 'J.-B.', '(1825–1889)'],
                ['ArbeauT', 'Arbeau', 'T.', '(1519–1595)'],
                ['ArchangelskyA', 'Archangelsky', 'A.', '(1846–1924)'],
                ['AriostiOA', 'Ariosti', 'O. A.', '(1666–1729)'],
                ['ArneT', 'Arne', 'T.', '(1710–1788)'],
                ['AscherJ', 'Ascher', 'J.', '(1829–1869)'],
                ['BachCPE', 'Bach', 'C. P. E.', '(1714–1788)'],
                ['BachJS', 'Bach', 'J. S.', '(1685–1750)'],
                ['BainJLM', 'Bain', 'J. L. M.', '(c.1840–1925)'],
                ['BaltzarT', 'Baltzar', 'T.', '(c.1631–1663)'],
                ['BanchieriA', 'Banchieri', 'A.', '(c.1567–1634)'],
                ['BanisterJ', 'Banister', 'J.', '(c.1624–1679)'],
                ['BanksJK', 'Banks', 'J. K.', '(1987–)'],
                ['BarbellaE', 'Barbella', 'E.', '(1718–1777)'],
                ['BartokB', 'Bartók', 'B.', '(1881–1945)'],
                ['BeethovenLv', 'Beethoven', 'L. V.', '(1770–1827)'],
                ['BehrF', 'Behr', 'F.', '(1837–1898)'],
                ['BendaJA', 'Benda', 'J. A.', '(1722–1795)'],
                ['BenoitP', 'Benoit', 'P.', '(1834–1901)'],
                ['BishopHR', 'Bishop', 'H. R.', '(1786–1855)'],
                ['BizetG', 'Bizet', 'G.', '(1838–1875)'],
                ['BlakeB', 'Blake', 'B.', '(1751–1827)'],
                ['BlissPP', 'Bliss', 'P. P.', '(1838–1876)'],
                ['BlumenthalJ', 'Blumenthal', 'J.', '(1829–1908)'],
                ['BoismortierJBd', 'Boismortier', 'J. B. de', '(1689–1755)'],
                ['BortnianskyD', 'Bortniansky', 'D.', '(1751–1825)'],
                ['BourgeoisL', 'Bourgeois', 'L.', '(c.1510–1560)'],
                ['BradburyWB', 'Bradbury', 'W. B.', '(1816–1868)'],
                ['BrahmsJ', 'Brahms', 'J.', '(1833–1897)'],
                ['BreyC', 'Brey', 'C.', '(1954–)'],
                ['BrownCJ', 'Brown', 'C. J.', '(1947–)'],
                ['BruchM', 'Bruch', 'M.', '(1838–1920)'],
                ['BrucknerA', 'Bruckner', 'A.', '(1824–1896)'],
                ['BurgmullerJFF', 'Burgmüller', 'J. F. F.', '(1806–1874)'],
                ['BuxtehudeD', 'Buxtehude', 'D.', '(c.1637–1707)'],
                ['CarcassiM', 'Carcassi', 'M.', '(1792–1853)'],
                ['CareyH', 'Carey', 'H.', '(1687?–1743)'],
                ['CarulliF', 'Carulli', 'F.', '(1770–1841)'],
                ['CaudiosoD', 'Caudioso', 'D.', '(17??–?)'],
                ['CavalliniE', 'Cavallini', 'E.', '(1807–1874)'],
                ['CecereC', 'Cecere', 'C.', '(1706–1761)'],
                ['CeresiniG', 'Ceresini', 'G.', '(1584–1659)'],
                ['ChabrierEA', 'Chabrier', 'E. A.', '(1841–1894)'],
                ['CharpentierMA', 'Charpentier', 'M.-A.', '(1643–1704)'],
                ['ChopinFF', 'Chopin', 'F. F.', '(1810–1849)'],
                ['Claribel', 'Claribel [C. A. Barnard ]', '', '(1830–1869)'],
                ['ClarkFS', 'Clark', 'F. S.', '(1840–1883)'],
                ['ClementiM', 'Clementi', 'M.', '(1752–1832)'],
                ['CocchiG', 'Cocchi', 'G.', '(1712–1796)'],
                ['ComeauO', 'Comeau', 'O.', '(1924–1971)'],
                ['CorelliA', 'Corelli', 'A.', '(1653–1713)'],
                ['CorneliusP', 'Cornelius', 'P.', '(1824–1874)'],
                ['CosteN', 'Coste', 'N.', '(1805–1883)'],
                ['CouperinF', 'Couperin', 'F.', '(1668–1733)'],
                ['CroftW', 'Croft', 'W.', '(1678–1727)'],
                ['CrottiA', 'Arcangelo Crotti', '', '(15??–1606)'],
                ['CrugerJ', 'Cruger', 'J.', '(1598–1662)'],
                ['CzernyC', 'Czerny', 'C.', '(1791–1857)'],
                ['DandrieuJ', 'Dandrieu', 'J.-F.', '(1681–1738)'],
                ['DebussyC', 'Debussy', 'C.', '(1862–1918)'],
                ['DelmetP', 'Delmet', 'P.', '(1862–1904)'],
                ['DevienneF', 'Devienne', 'F.', '(1759–1803)'],
                ['DiabelliA', 'Diabelli', 'A.', '(1781–1858)'],
                ['DickinsonCJ', 'Dickinson', 'C. J.', '(1822–1883)'],
                ['DoaneWH', 'Doane', 'W. H.', '(1832–1915)'],
                ['DonizettiG', 'Donizetti', 'G.', '(1797–1848)'],
                ['DoonanSC', 'Doonan', 'S. C.', '(1952–)'],
                ['DowlandJ', 'Dowland', 'J.', '(1563–1626)'],
                ['DukasP', 'Dukas', 'P.', '(1865–1935)'],
                ['DussekJL', 'Dussek', 'J. L.', '(1760–1812)'],
                ['DuyseFv', 'Van Duyse', 'F.', '(1843–1910)'],
                ['DvorakA', 'Dvořák', 'A.', '(1841–1904)'],
                ['DykesJB', 'Dykes', 'J. B.', '(1823–1876)'],
                ['EcclesH', 'Eccles', 'H.', '(1670–1742)'],
                ['ElgarE', 'Elgar', 'E.', '(1857–1934)'],
                ['EllorJ', 'Ellor', 'J.', '(1819–1899)'],
                ['ElveyGJ', 'Elvey', 'G. J.', '(1816–1893)'],
                ['EmmettDD', 'Emmett', 'D. D.', '(1815–1904)'],
                ['FarinelM', 'Farinel', 'M.', '(1649–1726)'],
                ['FaureG', 'Fauré', 'G.', '(1845–1924)'],
                ['FieldJ', 'Field', 'J.', '(1782–1837)'],
                ['FischerJKF', 'Fischer', 'J. K. F.', '(1665–1746)'],
                ['FosterSC', 'Foster', 'S. C.', '(1826–1864)'],
                ['FranckC', 'Franck', 'C.', '(1822–1890)'],
                ['FranzR', 'Franz', 'R.', '(1815–1862)'],
                ['FriedrichII', 'Friedrich II of Prussia', '', '(1712–1786)'],
                ['FrobergerJJ', 'Froberger', 'J. J.', '(1616–1667)'],
                ['FuchsR', 'Fuchs', 'R.', '(1847–1927)'],
                ['GabelloneG', 'Gabellone', 'G.', '(1727–1796)'],
                ['GalileiV', 'Galilei', 'V.', '(1520–1591)'],
                ['GastoldiG', 'Gastoldi', 'G.', '(1556–1622)'],
                ['GauntlettHJ', 'Gauntlett', 'H. J.', '(1805–1876)'],
                ['GershwinG', 'Gershwin', 'G.', '(1898–1937)'],
                ['GervasioGB', 'Gervasio', 'G. B.', '(c.1725–c.1785)'],
                ['GesualdoC', 'Gesualdo', 'C.', '(1566–1613)'],
                ['GibbonsO', 'Gibbons', 'O.', '(1583–1625)'],
                ['GigoutE', 'Gigout', 'E.', '(1844–1925)'],
                ['GiordanoG', 'Giordano', 'G.', '(1748–1798)'],
                ['GiardiniFd', 'Felice de Giardini', '', '(1716–1796)'],
                ['GiulianiM', 'Giuliani', 'M.', '(1781–1829)'],
                ['GiulianoG', 'Giuliano', 'G.', '(c.1750)'],
                ['GlaserCG', 'Glaser', 'C. G.', '(1784–1829)'],
                ['GlazunovA', 'Glazunov', 'A.', '(1865–1936)'],
                ['GloverCW', 'Glover', 'C. W.', '(1797–1868)'],
                ['GobbaertsL', 'Gobbaerts (L. Streabbog)', 'F. J.', '(1835-1886)'],
                ['GossecFJ', 'Gossec', 'F.-J.', '(1734–1829)'],
                ['GossJ', 'Goss', 'J.', '(1800–1880)'],
                ['GottschalkLM', 'Gottschalk', 'L. M.', '(1829–1869)'],
                ['GounodC', 'Gounod', 'C.', '(1818–1893)'],
                ['GrandiA', 'Grandi', 'A.', '(1577–1630)'],
                ['GreatorexHW', 'Greatorex', 'H. W.', '(1816–1853)'],
                ['GreiterM', 'Greiter', 'M.', '(1500–1552)'],
                ['GriegE', 'Grieg', 'E.', '(1843–1907)'],
                ['GrignyNd', 'Grigny', 'N. de  ', '(1672–1703)'],
                ['GruberFX', 'Gruber', 'F. X.', '(1787–1863)'],
                ['HallRB', 'Hall', 'R. B.', '(1858–1907)'],
                ['HanonCL', 'Hanon', 'C. L.', '(1819-1900)'],
                ['HandelGF', 'Handel', 'G. F.', '(1685–1759)'],
                ['HasseJA', 'Hasse', 'J. A.', '(1699–1783)'],
                ['HastingsT', 'Hastings', 'T.', '(1784–1872)'],
                ['HattonJ', 'Hatton', 'J.', '(?–1793)'],
                ['HaydnFJ', 'Haydn', 'F. J.', '(1732–1809)'],
                ['HaydnJM', 'Haydn', 'J. M.', '(1737–1806)'],
                ['HeiseP', 'Heise', 'P.', '(1830–1879)'],
                ['HildachE', 'Hildach', 'E.', '(1849–1924)'],
                ['HolstGT', 'Holst', 'G. T.', '(1874–1934)'],
                ['HoretzkyF', 'Horetzky', 'F.', '(1796–1870)'],
                ['HorsleyCE', 'Horsley', 'C. E.', '(1822–1876)'],
                ['HughesJ', 'Hughes', 'J.', '(1873–1932)'],
                ['HunterC', 'Hunter', 'C.', '(1876–1906)'],
                ['HullahJ', 'Hullah', 'J.', '(1812–1884)'],
                ['HumperdinckE', 'Humperdinck', 'E.', '(1873–1916)'],
                ['IlievGK', 'Iliev', 'G. K.', '(1977–)'],
                ['InallsJ', 'Inalls', 'J.', '(1764–1828)'],
                ['Ippolitov-IvanovM', 'Ippolitov-Ivanov', 'M.', '(1859–1935)'],
                ['JamesJ', 'James', 'J.', '(1833–1902)'],
                ['JanequinC', 'Janequin', 'C.', '(c.1485–1558)'],
                ['JapartJ', 'Japart', 'J.', '(fl. 1474–1507)'],
                ['JarmanT', 'Jarman', 'T.', '(1776–1861)'],
                ['JeffreysJ', 'Jeffreys', 'J.', '(1718–1798)'],
                ['JohnsonD', 'Johnson', 'D.', '(?–)'],
                ['JolyD', 'Joly', 'D.', '(?–1879)'],
                ['JoplinS', 'Joplin', 'S.', '(1868–1917)'],
                ['JudeWH', 'Jude', 'W. H.', '(1851–1922)'],
                ['KiallmarkGF', 'Kiallmark', 'G. F.', '(1804–1887)'],
                ['KeyperFJ', 'Keyper', 'F.J.', '(1756—1815)'],
                ['KnappPP', 'Knapp', 'P. P.', '(1839–1908)'],
                ['KnjzeF', 'Knjze', 'F.', '(1784–1840)'],
                ['KocherC', 'Kocher', 'C.', '(1786–1872)'],
                ['KoenigJB', 'Koenig', 'J. B.', '(1691–1758)'],
                ['KoppraschG', 'Kopprasch', 'G.', '(c.1800–c.1833)'],
                ['KopylovA', 'Kopylov', 'A.', '(1854–1911)'],
                ['Kruetzer', 'Kruetzer', '', '(?–?)'],
                ['KuffnerJ', 'Küffner', 'J.', '(1776–1856)'],
                ['KuhlauF', 'Kuhlau', 'F.', '(1786–1832)'],
                ['KuhnauJ', 'Kuhnau', 'J.', '(1660–1722)'],
                ['KuhnelA', 'Kuhnel', 'A.', '(1645–1700)'],
                ['KumarR', 'Kumar', 'R.', '(1988–)'],
                ['LaloE', 'Lalo', 'E.', '(1823–1892)'],
                ['LassusOd', 'de Lassus', 'O.', '(1530 or 1532–1594)'],
                ['LaubF', 'Laub', 'F.', '(1832–1875)'],
                ['LeoL', 'Leo', 'L.', '(1694–1744)'],
                ['LisztF', 'Liszt', 'F.', '(1811–1886)'],
                ['LottiA', 'Lotti', 'A.', '(c.1667–1740)'],
                ['LowryR', 'Lowry', 'R.', '(1826–1899)'],
                ['LullyJB', 'Lully', 'J. B.', '(1632–1687)'],
                ['LutherM', 'Luther', 'M.', '(1483–1546)'],
                ['MagnenatS', 'Magnenat', 'S.', '(1980–)'],
                ['MajorJ', 'Major', 'J.', '(?–?)'],
                ['ManciniF', 'Mancini', 'F.', '(1672–1737)'],
                ['MannAH', 'Mann', 'A. H.', '(1850–1929)'],
                ['MarcelloB', 'Marcello', 'B.', '(1686–1739)'],
                ['MarenzioL', 'Marenzio', 'L.', '(1553?–1599)'],
                ['MarshSB', 'Marsh', 'S. B.', '(1798–1875)'],
                ['MartiniGB', 'Martini', 'G. B.', '(1706–1784)'],
                ['MasonL', 'Mason', 'L.', '(1792–1872)'],
                ['MatiegkaWT', 'Matiegka', 'W. T.', '(1773–1830)'],
                ['MehulEN', 'Méhul', 'E. N.', '(1763–1817)'],
                ['Mendelssohn-BartholdyF', 'Mendelssohn-Bartholdy', 'F.', '(1809–1847)'],
                ['MercadanteS', 'Mercadante', 'S.', '(1795–1870)'],
                ['MertzJK', 'Mertz', 'J. K.', '(1806–1856)'],
                ['MessiterAH', 'Messiter', 'A. H.', '(1834–1916)'],
                ['MethfesselA', 'Methfessel', 'A.', '(1785–1869)'],
                ['MilanL', 'Milan', 'L.', '(1536–1561)'],
                ['MinkusLA', 'Minkus', 'L. A.', '(1826–1917)'],
                ['MonkWH', 'Monk', 'W. H.', '(1823–1889)'],
                ['MontePd', 'de Monte', 'P.', '(1521–1603)'],
                ['MonteverdiC', 'Monteverdi', 'C.', '(1567–1643)'],
                ['MooreT', 'Moore', 'T.', '(1779–1833)'],
                ['MorelandC', 'Moreland', 'C.', '(?–?)'],
                ['MozartWA', 'Mozart', 'W. A.', '(1756–1791)'],
                ['MuellerAE', 'Müller', 'A. E.', '(1767–1817)'],
                ['MuellerW', 'Müller', 'W.', '(1767–1835)'],
                ['MuffatG', 'Muffat', 'G.', '(1653–1704)'],
                ['MullenJW', 'Mullen', 'J. W.', '(?–?)'],
                ['MurrayJR', 'Murray', 'J. R.', '(1841–1905)'],
                ['MussorgskyM', 'Mussorgsky', 'M.', '(1839–1881)'],
                ['NaujalisJ', 'Naujalis', 'J.', '(1869–1934)'],
                ['NeithardtA', 'Neithardt', 'A.', '(1793–1861)'],
                ['NeumarkG', 'Neumark', 'G.', '(1621–1681)'],
                ['NicolaiP', 'Nicolai', 'P.', '(?–?)'],
                ['NielsenCA', 'Nielsen', 'C. A.', '(1865–1931)'],
                ['PachelbelJ', 'Pachelbel', 'J.', '(1653–1706)'],
                ['PaganiniN', 'Paganini', 'N.', '(1782–1840)'],
                ['PapezikR', 'Papezik', 'R.', '(1974–)'],
                ['PeaceAL', 'Peace', 'A. L.', '(1844–1912)'],
                ['PeaseAH', 'Pease', 'A. H.', '(1838–1882)'],
                ['PejacsevichD', 'Pejacsevich', 'D.', '(1885–1923)'],
                ['PergolesiGB', 'Pergolesi', 'G. B.', '(1710–1736)'],
                ['PezeliusJ', 'Pezelius', 'J.', '(1639–1694)'],
                ['PleyelIJ', 'Pleyel', 'I. J.', '(1757–1831)'],
                ['PorporaN', 'Porpora', 'N.', '(1686–1768)'],
                ['Powlwheel', 'Powlwheel', 'Mr.', '(?–?)'],
                ['PresJd', 'des Prés', 'J.', '(c.1440–1521)'],
                ['PriuliG', 'Priuli', 'G.', '(15??–16??)'],
                ['PurcellH', 'Purcell', 'H.', '(1658–1695)'],
                ['QuantzJJ', 'Quantz', 'J. J.', '(1830–1908)'],
                ['RachmaninoffS', 'Rachmaninoff', 'S.', '(1873-1943)'],
                ['RameauJP', 'Rameau', 'J. P.', '(1683–1764)'],
                ['Reddings', 'Reddings', 'Mr.', '(?–?)'],
                ['RednerLH', 'Redner', 'L. H.', '(1784–1838)'],
                ['RegerM', 'Reger', 'M.', '(1873–1916)'],
                ['RiedingO', 'Rieding', 'O.', '(1840–1918)'],
                ['RiesF', 'Ries', 'F.', '(1844–1908)'],
                ['Rimsky-KorsakovN', 'Rimsky-Korsakov', 'N.', '(1645?–1725?)'],
                ['RitterC', 'Ritter', 'C.', '(1624–1680)'],
                ['RoberdayF', 'Roberday', 'F.', '(1820–1895)'],
                ['RollaA', 'Rolla', 'A.', '(1757–1841)'],
                ['RootGF', 'Root', 'G. F.', '(1792–1868)'],
                ['RossiniG', 'Rossini', 'G.', '(1705–1755)'],
                ['RougetdeLisleCJ', 'Rouget de Lisle', 'C. J.', '(1760–1836)'],
                ['RoyerJNP', 'Royer', 'J.-N.-P.', '(1840–1916)'],
                ['RudorffE', 'Rudorff', 'E.', '(1835–1921)'],
                ['Saint-SaensC', 'Saint-Saëns', 'C.', '(1600–1679)'],
                ['SancesGF', 'Sances', 'G. F.', '(1640–1710)'],
                ['SanzG', 'Sanz', 'G.', '(1979–)'],
                ['SardainL', 'Sardain', 'L.', '(c.1595–1663)'],
                ['SatieE', 'Satie', 'E.', '(1866–1925)'],
                ['ScarlattiD', 'Scarlatti', 'D.', '(1685–1757)'],
                ['ScheidemannH', 'Scheidemann', 'H.', '(c.1623–1680)'],
                ['SchmelzerJH', 'Schmelzer', 'J. H.', '(c.1590–c.1665)'],
                ['SchopJ', 'Schop', 'J.', '(1841–1897)'],
                ['SchreckG', 'Schreck', 'G.', '(1849–1918)'],
                ['SchubertF', 'Schubert', 'F.', '(1797–1828)'],
                ['SchulzJAP', 'Schulz', 'J. A. P.', '(1747–1800)'],
                ['SchumannR', 'Schumann', 'R.', '(1810–1856)'],
                ['ScottCHF', 'Scott', 'C. H. F.', '(1826–1888)'],
                ['ScriabinA', 'Scriabin', 'A.', '(1872–1915)'],
                ['SherwinWF', 'Sherwin', 'W. F.', '(1989–)'],
                ['SidwellA', 'Sidwell', 'A.', '(1850–1922)'],
                ['SilcherF', 'Silcher', 'F.', '(1789–1860)'],
                ['SittH', 'Sitt', 'H.', '(1813–1879)'],
                ['SmallwoodW', 'Smallwood', 'W.', '(1831–1897)'],
                ['SmartHT', 'Smart', 'H. T.', '(1854–1932)'],
                ['SorF', 'Sor', 'F.', '(1778–1839)'],
                ['SousaJP', 'Sousa', 'J. P.', '(?–?)'],
                ['Spagnoletti', 'Spagnoletti', '', '(1636–1707)'],
                ['SpeerD', 'Speer', 'D.', '(1822–1905)'],
                ['SpohrL', 'Spohr', 'L.', '(1784–1859)'],
                ['StainerJ', 'Stainer', 'J.', '(1840–1901)'],
                ['StanchinskyAV', 'Stanchinsky', 'A. V.', '(1888–1914)'],
                ['StraussF', 'Strauss', 'F.', '(1842–1900)'],
                ['StraussJJ', 'Strauss Jr.', 'J.', '(1825–1899)'],
                ['SullivanA', 'Sullivan', 'A.', '(1973–)'],
                ['SuterH', 'Suter', 'H.', '(1870–1926)'],
                ['SzervacA', 'Szervác', 'A.', '(1510–1585)'],
                ['TallisT', 'Tallis', 'T.', '(1681–1767)'],
                ['TarregaF', 'Tarrega', 'F.', '(1852–1909)'],
                ['TchaikovskyPI', 'Tchaikovsky', 'P. I.', '(1840–1893)'],
                ['TelemannGP', 'Telemann', 'G. P.', '(1584–1635)'],
                ['TeschnerM', 'Teschner', 'M.', '(1837–1909)'],
                ['TiddemanM', 'Tiddeman', 'M.', '(1858–1913)'],
                ['TitelouzeJ', 'Titelouze', 'J.', '(1563–1633)'],
                ['TourjeeLE', 'Tourjee', 'L. E.', '(1833–1896)'],
                ['TownerDB', 'Towner', 'D. B.', '(1873–1922)'],
                ['Traditional', 'Traditional', '', ''],
                ['TurpinT', 'Turpin', 'T.', '(1582/83–1649)'],
                ['UgolinoV', 'Ugolino', 'V.', '(?–?)'],
                ['ValentiniG', 'Valentini', 'G.', '(1585–1661)'],
                ['ValvasensiLG', 'Valvasensi', 'L. G.', '(?–?)'],
                ['VeliumovA', 'Veliumov', 'A.', '(1813–1901)'],
                ['VerdiG', 'Verdi', 'G.', '(1549–1611)'],
                ['VictoriaTLd', 'de Victoria', 'T. L.', '(1697–1773)'],
                ['VidalPA', 'Vidal', 'P. A.', '(1863–1931)'],
                ['VinciL', 'Vinci', 'L.', '(1690–1730)'],
                ['VitaliF', 'Vitali', 'F.', '(ca. 1599–1653)'],
                ['VivaldiA', 'Vivaldi', 'A.', '(1678–1741)'],
                ['VolkmannR', 'Volkmann', 'R.', '(1815–1883)'],
                ['WadeJF', 'Wade', 'J. F.', '(1711–1786)'],
                ['WanhalJ', 'Wanhal', 'J.', '(1739–1813)'],
                ['WeckmannM', 'Weckmann', 'M.', '(1621–1674)'],
                ['WeelkesT', 'Weelkes', 'T.', '(1576–1623)'],
                ['WernerH', 'Werner', 'H.', '(1800–1833)'],
                ['WidorC', 'Widor', 'C.', '(1845–1937)'],
                ['WilliamsR', 'Williams', 'R.', '(1782–1818)'],
                ['WilliamsRH', 'Williams', 'R. H.', '(1805–1876)'],
                ['WillisRS', 'Willis', 'R. S.', '(1819–1900)'],
                ['WittCF', 'Witt', 'C. F.', '(1660–1716)'],
                ['WorrallH', 'Worrall', 'H.', '(1825–1902)'],
                ['WyethJ', 'Wyeth', 'J.', '(1770–1858)'],
                ['Yaniewicz', 'Yaniewicz', '', '(1762–1848)'],
                ['ZanoniM', 'Zanoni', 'M.', '(1964–)']]

composerLookupNewAdds = {}
for c in composerList:
    # no dates in this listing, keep it simple
    composerLookupNewAdds[c[0]] = '{0} {1}'.format(c[2], c[1])


count = 0
missingComposers = set()

with open(fullCSV, newline='') as source:
    reader = csv.DictReader(source)
    for row in reader:

        if row['mutopiacomposer'] not in composerLookupNewAdds:
            missingComposers.add(row['mutopiacomposer'])

        elif row['omit?'] != 'T' and row['new?'] == 'T':
            id = int(row['mutopia-id'])
            count += 1
            print(
                # count,
                # row['mutopia-id'],
                # int(row['mutopia-id']) in oldIds,
                # row['mutopiacomposer'],
                composerLookupNewAdds[row['mutopiacomposer']] +  ' | ' +
                row['cn-title'] + ' | ' +
                row['cn-instrument'])

print(str(count) + ' new additions.')
if len(missingComposers) > 0:
    print('PROBLEM: MISSING COMPOSERS:')
    print(missingComposers)
else:
    print('No missing composers.')
print('Done with new additions report, beginning JSON generation.\n')

# END OF NEW ADDS REPORT GENERATION


# BEGIN JSON GENERATION

styleList = ['Baroque',
             'Classical',
             'Folk',
             'Gospel',
             'Hymn',
             'Jazz',
             'March',
             'Modern',
             'PopularDance',
             'Renaissance',
             'Romantic',
             'Song',
             'Technique']

instrumentList = ['Accordion',
                  'Bagpipe',
                  'Bass',
                  'Basso-continuo',
                  'Bassoon',
                  'Brass-ensemble',
                  'Cello',
                  'Choir',
                  'Clarinet',
                  'Clavier',
                  'Double-bass',
                  'Ensemble',
                  'Flute',
                  'Guitar',
                  'Harmonium',
                  'Harp',
                  'Harpsichord',
                  'Horn',
                  'Koto',
                  'Lute',
                  'Mandolin',
                  'Oboe',
                  'Orchestra',
                  'Organ',
                  'Percussion',
                  'Piano',
                  'Recorder',
                  'Shakuhachi',
                  'Shamisen',
                  'String-ensemble',
                  'String-quartet',
                  'Timpani',
                  'Trombone',
                  'Trumpet',
                  'Vihuela',
                  'Viol',
                  'Viola',
                  'Violin',
                  'Voice',
                  'Wind-ensemble']

twoWordInsts = ['Basso Continuo',
                'Brass Ensemble',
                'Double Bass',
                'String Ensemble',
                'String Quartet',
                'Wind Ensemble',
                'double bass']

inst_regex = re.compile('[a-zA-Z\-]+')

noInstrumentMatch = []
unrecognizedInstTokens = set()

# todo: Lute isn't found
# 'Lute / Theorbo / Vihuela'
# Vihuela

def instClassifier(mutopiainstrument, id):
    insts = []
    mutoInst = mutopiainstrument
    for i in twoWordInsts:
        if i in mutoInst:
            hyphenated = i.replace(" ", "-")
            mutoInst = mutoInst.replace(i, hyphenated)

    tokens = inst_regex.findall(mutoInst)
    for t in tokens:
        t = t.capitalize()
        if t.endswith('s') and not t.endswith('ss'):
            t = t[0:-1]
        if t in instrumentList:
            insts.append(t)
        else:
            unrecognizedInstTokens.add(t)

    if insts == []:
        noInstrumentMatch.append([id, mutoInst])
    # print(insts)
    return insts


instrumentTally = {}
styleTally = {}
composerTally = {}

with open(fullCSV, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    # recsObject - an object with ids as keys that map to arrays of data for each item
    recsObject = {}
    # recsIdArray - an array of mutopia ids ordered into the default sort order for 'browsing'
    recsSortedIds = []

    for row in reader:
        if row['omit?'] != 'T':

            # IDs for the ordered array
            recsSortedIds.append(int(row['mutopia-id']));

            # INSTRUMENTS
            insts = instClassifier(row['cn-instrument'], row['mutopia-id'])
            for i in insts:
                if i in instrumentTally:
                    instrumentTally[i] += 1
                else:
                    instrumentTally[i] = 1

            # STYLES
            # handle style 'Popular / Dance'
            stl = row['cn-style'].replace(' / ', '')
            if stl in styleTally:
                styleTally[stl] += 1
            else:
                styleTally[stl] = 1

            # COMPOSERS
            comp = row['mutopiacomposer']
            if comp in composerTally:
                composerTally[comp] += 1
            else:
                composerTally[comp] = 1

            multifile = (1 < len(row['filename'].split(',,, ')))

            recsObject[ int(row['mutopia-id']) ] = [
                 stl,
                 comp, # 1
                 row['cn-title'],
                 insts, # 3
                 # instsCSS, # instrument classes
                 row['path'], # 4
                 False if multifile else row['filename'][:-3],
                 row['license-type'] + row['license-vsn'], # 6
                 row['cn-opus'],
                 row['cn-poet'], # 8
                 row['date'],
                 row['arranger'], # 10
                 ]

    out = json.dumps(recsObject)
    print('JSON parsed.')

    f = open(targetJSON, 'w')
    f.write('var recsjson = ' + out)
    f.write('\nvar recsSortedIds = ' + json.dumps(recsSortedIds))
    print('JSON saved.')


    # print(instrumentTally)
    print('\nEach piece has to have at least one instrument that is recognized.')
    print('Pieces with no instrument recognized (fix these):', sorted(noInstrumentMatch))

    print('\nA piece may have other instruments that are not recognized.  (Optionally add these.)')
    print('Unrecognized Instruments:', sorted(unrecognizedInstTokens))

    # composer lookup table also goes in json data file
    composerLookup = {}
    composerLookupText = ''

    for c in composerList:
        if c[0] in composerTally:
            composerLookup[c[0]] = ['{0} {1}'.format(c[2], c[1]), '{0}'.format(c[3])]

    composerLookupText = json.dumps(composerLookup)
    f.write('\nvar composerLookup = ' + composerLookupText)

    print('\nComposerLookup saved in JS file.')



# OUTPUT CHECKBOXES HTML

htmlOut = ''
ulOpen = '<ul class="filter-panel">\n'
ulClose = '</ul>\n\n'
formCloseDivClose = '</form>\n</div>\n\n'
liAlphabetA = '<li class="filter-panel-header">'
liAlphabetB = '</li>\n'


## STYLES

styleGroupSize = 6
styleShortList = list(filter(lambda x: x in styleTally, styleList))
count = 0
htmlOut += '<div id="style-filters" class="filters">\n'
# todo: when needed handle PopularDance --> 'Popular / Dance'
htmlOut += '<h3 class="filter-panel-header-main">Filter by Style</h3>\n'
htmlOut += '<span class="filter-panel-select-all"><a id="s-all">Select All</a> &nbsp; <a id="s-none">Deselect All</a></span>\n'
htmlOut += '<form name="style-form" id="style-form">\n\n'
htmlOut += ulOpen
for s in styleShortList:
    htmlOut += '<li><input type="checkbox" name="s-box" id="{0}" /><a class="f-link">{0} [{1}]</a></li>\n'.format(s, styleTally[s])
    count += 1
    if count % styleGroupSize == 0:
        htmlOut += ulClose + ulOpen
htmlOut += ulClose
htmlOut += formCloseDivClose


## INSTRUMENTS

instrumentGroupSize = 9
instrumentShortList = list(filter(lambda x: x in instrumentTally, instrumentList))
count = 0
htmlOut += '<div id="instrument-filters" class="filters">\n'
htmlOut += '<h3 class="filter-panel-header-main">Filter by Instrument</h3>\n'
htmlOut += '<span class="filter-panel-select-all"><a id="i-all">Select All</a> &nbsp; <a id="i-none">Deselect All</a></span>\n'
htmlOut += '<form name="instrument-form" id="instrument-form">\n\n'
htmlOut += ulOpen
for i in instrumentShortList:
    htmlOut += '<li><input type="checkbox" name="i-box" id="{0}" /><a class="f-link">{0} [{1}]</a></li>\n'.format(i, instrumentTally[i])
    count += 1
    if count % instrumentGroupSize == 0:
        htmlOut += ulClose + ulOpen
htmlOut += ulClose
htmlOut += formCloseDivClose


## COMPOSERS

composerGroupSize = 10
composerShortList = list(filter(lambda x: x[0] in composerTally, composerList))
compShortestList  = list(map(lambda x: x[0], composerShortList))

# fromLetters and toLetters contain lists of the letters that go in the alphabetical headings for each group
# fromLetters = the first letter and every nth letter beyond that
# toLetters = the (nth - 1) letter and every nth letter beyond that
# we just delete them off the front of the list as they are used
fromLetters       = list(map(lambda x: x[0], compShortestList[::composerGroupSize]))
toLetters         = list(map(lambda x: x[0], compShortestList[(composerGroupSize - 1)::composerGroupSize]))
toLetters.append(compShortestList[-1:][0][0])
count = 0

htmlOut += '<div id="composer-filters" class="filters">\n'
htmlOut += '<h3 class="filter-panel-header-main">Filter by Composer</h3>\n'
htmlOut += '<span class="filter-panel-select-all"><a id="c-all">Select All</a> &nbsp; <a id="c-none">Deselect All</a></span>\n'
htmlOut += '<form name="composer-form" id="composer-form">\n\n'

for c in composerShortList:
    if count % composerGroupSize == 0 and len(fromLetters) > 0 and len(toLetters) > 0:
        if count == 0:
            htmlOut += ulOpen
        else:
            htmlOut += ulClose + ulOpen

        htmlOut += liAlphabetA + fromLetters[0] + ' - ' + toLetters[0] + liAlphabetB
        del fromLetters[0]
        del toLetters[0]

    htmlOut += '<li><input type="checkbox" name="c-box" id="{0}" /><a class="f-link">{1}, {2} {3} [{4}]</a></li>\n'.format(c[0], c[1], c[2], c[3], composerTally[c[0]])
    count += 1

htmlOut += ulClose
htmlOut += formCloseDivClose

h = open(targetHTML, 'w')
h.write(htmlOut)


'''
    unrecognized instrument tokens results:

    # April5-2016 ['Chamber', 'Male',
                   'Also', 'Alti', 'Amore', 'And', 'Baritone', 'Basset', 'Bassi', 'Basso', 'Classical', 'Clavichord', 'Continuo', 'D', 'Duet', 'F', 'For', 'French', 'In', 'Or', 'Sa', 'Satb', 'Solo', 'Soprani', 'Soprano', 'Tenor', 'Tenori', 'Transcribed', 'Triangle', 'Ttbb', 'Tttb', 'Two']

    # June17-2015 ['Also', 'Alti', 'Amore', 'And', 'Baritone', 'Basset', 'Bassi', 'Basso', 'Classical', 'Clavichord', 'Continuo', 'D', 'Duet', 'F', 'For', 'French', 'In', 'Or', 'Sa', 'Satb', 'Solo', 'Soprani', 'Soprano', 'Tenor', 'Tenori', 'Transcribed', 'Triangle', 'Ttbb', 'Tttb', 'Two']

    # June16-2015: {'Tttb', 'Soprano', 'Classical', 'F', 'Tenor', 'Alti', 'String', 'And', 'Clavichord', 'Ensemble', 'In', 'Satb', 'Baritone', 'D', 'Amore', 'For', 'Bassi', 'Basso', 'Continuo', 'Or', 'Ttbb', 'Transcribed', 'Tenori', 'French', 'Quartet', 'Sa', 'Basset', 'Two', 'Soprani', 'Also', 'Duet', 'Solo', 'Triangle'}

    # OLD {'Duet', 'For', 'Vihuela', 'Basso', 'Ttbb', 'Transcribed', 'Two', 'Sa', 'Tttb', 'And', 'Soprano', 'Clavichord', 'Satb', 'Continuo'}

'''


'''
#   "style", "mutopiacomposer", "composer", "mutopiatitle", "title", "mutopiainstrument", "instrument", "mutopia-id", "mutopiaopus", "opus", "mutopiapoet", "poet", "date", "source", "license-type", "license-vsn", "license", "copyright", "arranger", "footer", "version", "filename", "path"
'''

# see this script about csv to json in python
# http://www.andymboyle.com/2011/11/02/quick-csv-to-json-parser-in-python/
