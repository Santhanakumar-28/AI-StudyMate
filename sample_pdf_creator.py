import pymupdf as fitz
import os

def generate_sample_academic_pdf(output_path: str = "uploads/sample_machine_learning_primer.pdf") -> str:
    """
    Generates a rich, structured academic PDF on Artificial Intelligence & Machine Learning
    with authentic chapters, definitions, algorithms, and key examinable facts.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc = fitz.open()

    pages_content = [
        (
            "Chapter 1: Foundations of Artificial Intelligence & Machine Learning",
            [
                "Artificial Intelligence (AI) refers to the simulation of human intelligence in machines that are programmed to think and learn.",
                "Machine Learning (ML) is a subset of artificial intelligence that provides systems the ability to automatically learn and improve from experience without being explicitly programmed.",
                "The primary goal of machine learning is to allow computers to learn automatically without human intervention and adjust actions accordingly.",
                "Supervised learning is defined as a machine learning approach where models are trained on labelled data with known inputs and correct target outputs.",
                "Unsupervised learning refers to learning algorithms that identify hidden patterns or intrinsic structures within unlabelled datasets.",
                "Reinforcement learning is an agent-centric learning paradigm where an agent learns to achieve a goal by interacting with a dynamic environment and receiving rewards or penalties."
            ]
        ),
        (
            "Chapter 2: Supervised Learning & Classification Algorithms",
            [
                "Linear Regression is an algorithm used for predicting continuous numerical values based on linear relationships between independent and dependent variables.",
                "Logistic Regression is a classification algorithm used to estimate the probability of binary categorical outcomes using a sigmoid activation function.",
                "Decision Tree is a non-parametric supervised learning algorithm that partitions data into subsets based on feature threshold tests.",
                "Overfitting occurs when a statistical model learns the detail and noise in the training data to the extent that it negatively impacts the performance on new unseen data.",
                "Random Forest is an ensemble learning method that constructs a multitude of decision trees at training time and outputs the mode or mean prediction.",
                "Gradient Boosting operates by sequentially training weak predictive models such that each new model directly corrects the residual errors of prior iterations."
            ]
        ),
        (
            "Chapter 3: Model Evaluation, Metrics & Neural Networks",
            [
                "Precision refers to the proportion of true positive predictions among all positive predictions made by the classifier.",
                "Recall is defined as the proportion of actual positive cases that were correctly identified by the classification model.",
                "The F1 Score is calculated as the harmonic mean of precision and recall to provide a balanced metric on imbalanced datasets.",
                "Backpropagation is an optimization algorithm that calculates the gradient of the loss function with respect to neural network weights using the chain rule.",
                "Convolutional Neural Networks (CNNs) are specialized deep neural architectures designed for processing grid-structured data such as digital images.",
                "Recurrent Neural Networks (RNNs) consist of cyclical connections that enable the persistence of sequential context and temporal dependencies."
            ]
        ),
        (
            "Chapter 4: Optimization, Regularization & Advanced Architectures",
            [
                "Stochastic Gradient Descent (SGD) optimizes objective functions by computing parameter updates on individual mini-batches rather than the entire dataset.",
                "L1 Regularization (Lasso) adds a penalty equal to the absolute value of the magnitude of coefficients, promoting sparse feature representations.",
                "L2 Regularization (Ridge) adds a squared magnitude penalty to weight coefficients to prevent extreme weight values and reduce variance.",
                "The Attention Mechanism enables neural architectures to dynamically focus on specific segments of input sequences regardless of their positional distance.",
                "Transformer architecture relies entirely on self-attention mechanisms to compute representations of its inputs and outputs without using sequence-aligned RNNs.",
                "Cross-Validation is a statistical resampling procedure used to evaluate machine learning models on limited data samples and guard against validation bias."
            ]
        )
    ]

    for title, sentences in pages_content:
        page = doc.new_page(width=595, height=842)  # A4 size
        
        # Header banner
        page.draw_rect(fitz.Rect(40, 40, 555, 80), color=(0.31, 0.27, 0.9), fill=(0.95, 0.95, 1.0))
        page.insert_text(fitz.Point(55, 65), title, fontsize=13, fontname="helv", color=(0.15, 0.12, 0.6))
        
        # Body content
        y = 120
        for s in sentences:
            # Bullet point symbol
            page.draw_circle(fitz.Point(55, y - 4), 2.5, color=(0.31, 0.27, 0.9), fill=(0.31, 0.27, 0.9))
            # Text block
            rect = fitz.Rect(68, y - 12, 540, y + 50)
            rc = page.insert_textbox(rect, s, fontsize=10.5, fontname="helv", color=(0.1, 0.15, 0.2), lineheight=1.4)
            y += 85

        # Footer
        page.insert_text(fitz.Point(40, 800), "AI StudyMate Academic Resource — Standard Educational Reference", fontsize=8.5, color=(0.5, 0.5, 0.6))
        page.insert_text(fitz.Point(520, 800), f"Page {len(doc)}", fontsize=8.5, color=(0.5, 0.5, 0.6))

    doc.save(output_path)
    doc.close()
    return output_path

if __name__ == "__main__":
    path = generate_sample_academic_pdf()
    print(f"Sample PDF generated at: {path}")
