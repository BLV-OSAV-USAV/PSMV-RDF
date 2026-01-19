```mermaid
classDiagram

class Product {
  eidgZulassungsnummer
  isNonProfessionallyAllowed
  soldoutDeadline
  exhaustionDeadline
}

class ChemicalProduct
class BiologicalControlAgent

Product <|-- ChemicalProduct
Product <|-- BiologicalControlAgent

class ParallelImport {
  foreignAdmissionNumber
}

Product <|-- ParallelImport
ParallelImport --> Product : referenceProduct

class SellingPermission {
  validFrom
  validTo
}

SellingPermission --> Product : permitsSaleOf
SellingPermission --> Organization : heldBy

class Organization {
  legalName
}

class Indication {
  dosage
  waitingPeriod
}

Product --> Indication : hasIndication

Indication --> CropGroup
Indication --> CropStressor
Indication --> ApplicationArea

class CropGroup
class CropStressor
class ApplicationArea

class Substance
class ComponentPortion

ChemicalProduct --> ComponentPortion
ComponentPortion --> Substance
ComponentPortion --> Role

class Role {
  ActiveIngredient
  Safener
  Synergist
  Additive
}

class Notice
class HazardStatement
class Obligation
class ApplicationComment

Product --> Notice
Indication --> Notice

Notice <|-- HazardStatement
Notice <|-- Obligation
Notice <|-- ApplicationComment

```
