<script>
    export let questions = [];

    let activeQuestion = null;

    function toggleQuestion(index) {
        activeQuestion = activeQuestion === index ? null : index;
    }
</script>

<section class="faq">
    <h2>Frequently Asked Questions</h2>
    {#each questions as question, index}
        <button
            class="faqbox"
            on:click={() => toggleQuestion(index)}
            aria-expanded={activeQuestion === index}
            type="button"
        >
            <svg
                class="icon"
                class:rotated={activeQuestion === index}
                width="24"
                height="24"
                fill="none"
                stroke="currentColor"
                xmlns="http://www.w3.org/2000/svg"
            >
                <path d="M6 9l6 6 6-6" />
            </svg>
            <span>{question.title}</span>
        </button>
        {#if activeQuestion === index}
            <div class="faq-content">
                <p>{question.content}</p>
            </div>
        {/if}
    {/each}
</section>

<style>
    .faq {
        padding: 80px 150px;
        background-color: #111;
        color: white;
        position: relative;
    }

    .faq h2 {
        font-size: 2.2rem;
        text-align: center;
        margin-bottom: 40px;
        font-family: 'Netflix Sans', 'Helvetica Neue', 'Segoe UI', 'Roboto', 'Ubuntu', sans-serif;
        color: #ffffff;
        font-weight: 600;
    }

    .faqbox {
        display: flex;
        align-items: center;
        width: 100%;
        max-width: 900px;
        margin: 0 auto 8px;
        padding: 20px;
        background: #111;
        cursor: pointer;
        border: none;
        color: white;
        font-size: 1.1rem;
        border-bottom: 1px solid #333;
        font-family: 'Netflix Sans', 'Helvetica Neue', 'Segoe UI', 'Roboto', 'Ubuntu', sans-serif;
        transition: all 0.3s ease;
        border-radius: 4px;
    }

    .faqbox:hover {
        background: rgba(255, 255, 255, 0.02);
        border-bottom-color: #098577;
    }

    .faqbox:hover .icon {
        stroke: #098577;
    }

    .faqbox svg {
        margin-right: 20px;
        transition: all 0.3s ease;
        flex-shrink: 0;
    }

    .faqbox svg.rotated {
        transform: rotate(180deg);
    }

    .faqbox span {
        text-align: left;
        flex: 1;
        font-weight: 500;
    }

    .faq-content {
        max-width: 900px;
        margin: 0 auto 20px;
        padding: 20px 25px;
        background: #1a1a1a;
        border-left: 3px solid #098577;
        font-family: 'Netflix Sans', 'Helvetica Neue', 'Segoe UI', 'Roboto', 'Ubuntu', sans-serif;
        color: rgba(255, 255, 255, 0.9);
        line-height: 1.6;
        border-radius: 0 4px 4px 0;
    }

    @media (max-width: 768px) {
        .faq {
            padding: 60px 20px;
        }
        
        .faq h2 {
            font-size: 1.8rem;
        }
        
        .faqbox {
            font-size: 1rem;
            padding: 18px;
        }
        
        .faq-content {
            padding: 18px 20px;
        }
    }
</style>
